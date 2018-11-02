# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""The Synchronization API."""

import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.decorators import protected_resource

from expenses.models import Category, DeletionRecord, DATA_MODELS, STR_TO_DATA_MODEL_MAP
from expenses.utils import parse_dt


def hello(_request):
    return JsonResponse({
        'auth_url': reverse('oauth2_provider:authorize'),
        'token_url': reverse('oauth2_provider:token'),
    })


@method_decorator([protected_resource(), csrf_exempt], name='dispatch')
class PostJsonEndpoint(View):
    def get(self, _request):
        return JsonResponse({"error": "Only POST requests allowed"}, status=400)

    def post(self, request):
        try:
            req_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "POST data must be JSON"}, status=400)

        out, status = self.get_response(request, req_data)
        return JsonResponse(out, status=status)

    def get_response(self, request, req_data: dict) -> (dict, int):
        raise NotImplementedError()


@protected_resource()
def profile(request):
    return JsonResponse({
        "full_name": request.user.get_full_name() or request.user.get_username(),
    })


class RunEndpoint(PostJsonEndpoint):
    def get_response(self, request, req_data: dict):
        now = timezone.now()
        out = {
            "sync_date": now.isoformat(),
            "deletions": {
                "new": [],
                "ack": [],
                "not_found": [],
            },
            "changes": {
                "new": {},
                "ack": {},
                "deleted": [],
                "not_found": [],
            }
        }

        for _, model_str in DATA_MODELS:
            out["changes"]["new"][model_str] = []
            out["changes"]["ack"][model_str] = []

        if req_data["last_sync"] is None:
            # Initial sync, provide all data
            for model, model_str in DATA_MODELS:
                queryset = model.objects.filter(user=request.user, date_modified__lte=now).order_by('id')
                out["changes"]["new"][model_str] = [o.to_json() for o in queryset]
            return JsonResponse(out)

        last_sync = parse_dt(req_data["last_sync"])
        # Find deletions
        out["deletions"]["new"] = [
            {"model": o.model, "id": o.object_pk}
            for o in DeletionRecord.objects.filter(
                user=request.user, date__gt=last_sync, date__lte=now)
        ]

        # And handle provided deletions
        for deletion in req_data.get("deletions", {}):
            model_cls = STR_TO_DATA_MODEL_MAP[deletion["model"]]
            try:
                obj = model_cls.objects.get(user=request.user, pk=deletion["id"])
                obj.delete_at(now)
                out["deletions"]["ack"].append(deletion)
            except ObjectDoesNotExist:
                # maybe it was deleted before?
                try:
                    DeletionRecord.objects.get(
                        user=request.user, model=deletion["model"], object_pk=deletion["id"])
                    out["deletions"]["ack"].append(deletion)
                except ObjectDoesNotExist:
                    # oh well, that is not exected
                    out["deletions"]["not_found"].append(deletion)

        # Handle new data from the user
        for model, model_str in DATA_MODELS:
            for change in req_data.get("changes", {}).get(model_str, []):
                if change.get("id") is None:
                    # add
                    obj = model(user=request.user)
                else:
                    try:
                        obj = model.objects.get(user=request.user, pk=change["id"])
                    except ObjectDoesNotExist:
                        nf_marker = {"model": model_str, "id": change["id"]}
                        try:
                            DeletionRecord.objects.get(
                                user=request.user, model=model_str, object_pk=change["id"])
                            out["changes"]["deleted"].append(nf_marker)
                        except DeletionRecord.DoesNotExist:
                            out["changes"]["not_found"].append(nf_marker)
                        continue

                obj.from_json(change, now)
                obj.save()
                out["changes"]["ack"][model_str].append({
                    "local_id": change["local_id"],
                    "id": obj.pk
                })

        # And give them our new data
        for model, model_str in DATA_MODELS:
            queryset = model.objects.filter(user=request.user, date_modified__gt=last_sync, date_modified__lte=now).order_by('id')
            out["changes"]["new"][model_str] = [o.to_json() for o in queryset]

        return out, 200


# Categories should not be synchronized in the usual way, since it doesn’t make much sense.
class CategoryAddEndpoint(PostJsonEndpoint):
    def get_response(self, request, req_data: dict):
        cat = Category(name=req_data["name"], order=req_data["order"])
        cat.save()
        return {"success": True}, 200


class CategoryEditEndpoint(PostJsonEndpoint):
    def get_response(self, request, req_data: dict):
        try:
            cat = Category.objects.get(pk=req_data["id"], user=request.user)
            cat.name = req_data["name"]
            cat.order = req_data["order"]
        except (KeyError, Category.DoesNotExist):
            return {"success": False, "error": "Bad request data."}, 400
        cat.save()
        return {"success": True}, 200


class CategoryDeleteEndpoint(PostJsonEndpoint):
    def get_response(self, request, req_data: dict):
        try:
            cat = Category.objects.get(pk=req_data["id"], user=request.user)
        except (KeyError, Category.DoesNotExist):
            return {"success": False, "error": "Bad request data."}, 400

        prep_success = cat.prepare_deletion(req_data["move_destination"], request.user)
        if prep_success:
            cat.delete()
        return {"success": prep_success}, 200 if prep_success else 500
