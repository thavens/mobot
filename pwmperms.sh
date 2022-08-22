#!/bin/sh

PWM=/sys/class/pwm/pwmchip0

echo 0 > ${PWM}/export
echo 1 > ${PWM}/export

chown -R root:gpio $PWM/*
chmod -R g+rwX $PWM/*