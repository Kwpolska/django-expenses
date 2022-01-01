/*
 * Expenses FlickMenu
 * Copyright © 2018-2022, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */

let touchStarts: any = {};
const DISTANCE = 100;

export default function setUpFlickMenu() {
    document.body.addEventListener("touchstart", (ev: TouchEvent) => {
        for (var i = 0; i < ev.changedTouches.length; i++) {
            let touch = ev.changedTouches[i];
            if (touch.pageX <= 20) {
                touchStarts[touch.identifier] = touch.pageX;
            }
        }
    });

    document.body.addEventListener("touchmove", (ev: TouchEvent) => {
        for (var i = 0; i < ev.changedTouches.length; i++) {
            let touch = ev.changedTouches[i];
            if (touchStarts.hasOwnProperty(touch.identifier)) {
                let startX = touchStarts[touch.identifier];
                if ((touch.pageX - touchStarts[touch.identifier]) >= DISTANCE) {
                    $(".navbar-collapse").collapse('show');
                    window.scrollTo(0, 0);
                    delete touchStarts[touch.identifier];
                }
            }
        }
    });

    document.body.addEventListener("touchend", (ev: TouchEvent) => {
        for (var i = 0; i < ev.changedTouches.length; i++) {
            let touch = ev.changedTouches[i];
            if (touchStarts.hasOwnProperty(touch.identifier)) {
                let startX = touchStarts[touch.identifier];
                if ((touch.pageX - touchStarts[touch.identifier]) >= DISTANCE) {
                    $(".navbar-collapse").collapse('show');
                    window.scrollTo(0, 0);
                }
                delete touchStarts[touch.identifier];
            }
        }
    });
}
