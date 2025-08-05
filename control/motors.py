# control/motors.py

import time

# --- Mock RPi.GPIO module for testing on Windows ---
# This class simulates the RPi.GPIO library so we can run the code
# on a non-Raspberry Pi machine without an ImportError.
# It prints the GPIO commands instead of executing them.
class MockGPIO:
    BCM = 11
    OUT = 1
    HIGH = 1
    LOW = 0

    def __init__(self):
        self.pins = {}
        self.pwm_channels = {}
    
    def setmode(self, mode):
        print(f"GPIO: Setting mode to {mode}")
    
    def setup(self, pin, mode):
        self.pins[pin] = mode
        print(f"GPIO: Setting up pin {pin} as {'OUTPUT' if mode == self.OUT else 'INPUT'}")

    def output(self, pin, value):
        print(f"GPIO: Setting pin {pin} to {value}")

    def PWM(self, pin, frequency):
        print(f"GPIO: Initializing PWM on pin {pin} with frequency {frequency}Hz")
        return self.MockPWM(pin)

    def cleanup(self):
        print("GPIO: Cleaning up pins.")

    class MockPWM:
        def __init__(self, pin):
            self.pin = pin
        
        def start(self, duty_cycle):
            print(f"GPIO: Starting PWM on pin {self.pin} with duty cycle {duty_cycle}%")

        def ChangeDutyCycle(self, duty_cycle):
            print(f"GPIO: Changing PWM duty cycle on pin {self.pin} to {duty_cycle}%")

        def stop(self):
            print(f"GPIO: Stopping PWM on pin {self.pin}")


# --- The Real MotorController Class ---
class MotorController:
    """
    Controls the two DC motors using an L298N motor driver.
    """
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.IS_RASPBERRY_PI = True
            print("MotorController: Running on Raspberry Pi with real RPi.GPIO.")
        except (ImportError, RuntimeError):
            GPIO = MockGPIO()
            self.IS_RASPBERRY_PI = False
            print("MotorController: Running in simulation mode with MockGPIO.")
        
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)

        # Pin definitions for the L298N motor driver
        self.RIGHT_IN1 = 17
        self.RIGHT_IN2 = 27
        self.RIGHT_ENA = 22
        
        self.LEFT_IN3 = 23
        self.LEFT_IN4 = 24
        self.LEFT_ENB = 25

        self.GPIO.setup(self.RIGHT_IN1, self.GPIO.OUT)
        self.GPIO.setup(self.RIGHT_IN2, self.GPIO.OUT)
        self.GPIO.setup(self.RIGHT_ENA, self.GPIO.OUT)

        self.GPIO.setup(self.LEFT_IN3, self.GPIO.OUT)
        self.GPIO.setup(self.LEFT_IN4, self.GPIO.OUT)
        self.GPIO.setup(self.LEFT_ENB, self.GPIO.OUT)

        self.frequency = 1000
        self.right_pwm = self.GPIO.PWM(self.RIGHT_ENA, self.frequency)
        self.left_pwm = self.GPIO.PWM(self.LEFT_ENB, self.frequency)
        
        self.right_pwm.start(0)
        self.left_pwm.start(0)

        self.stop()
        
        print("MotorController: Initialization complete.")

    def set_speed(self, speed):
        duty_cycle = max(0, min(100, speed))
        self.right_pwm.ChangeDutyCycle(duty_cycle)
        self.left_pwm.ChangeDutyCycle(duty_cycle)
        print(f"MotorController: Setting motor speed to {duty_cycle}%.")

    def move_forward(self, speed=50):
        self.GPIO.output(self.RIGHT_IN1, self.GPIO.HIGH)
        self.GPIO.output(self.RIGHT_IN2, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN3, self.GPIO.HIGH)
        self.GPIO.output(self.LEFT_IN4, self.GPIO.LOW)
        self.set_speed(speed)
        print("MotorController: Moving forward.")

    def move_backward(self, speed=50):
        self.GPIO.output(self.RIGHT_IN1, self.GPIO.LOW)
        self.GPIO.output(self.RIGHT_IN2, self.GPIO.HIGH)
        self.GPIO.output(self.LEFT_IN3, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN4, self.GPIO.HIGH)
        self.set_speed(speed)
        print("MotorController: Moving backward.")

    def stop(self):
        self.GPIO.output(self.RIGHT_IN1, self.GPIO.LOW)
        self.GPIO.output(self.RIGHT_IN2, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN3, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN4, self.GPIO.LOW)
        self.set_speed(0)
        print("MotorController: Stopping.")

    def turn_left(self, speed=50):
        self.GPIO.output(self.RIGHT_IN1, self.GPIO.HIGH)
        self.GPIO.output(self.RIGHT_IN2, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN3, self.GPIO.LOW)
        self.GPIO.output(self.LEFT_IN4, self.GPIO.HIGH)
        self.set_speed(speed)
        print("MotorController: Turning left.")

    def turn_right(self, speed=50):
        self.GPIO.output(self.RIGHT_IN1, self.GPIO.LOW)
        self.GPIO.output(self.RIGHT_IN2, self.GPIO.HIGH)
        self.GPIO.output(self.LEFT_IN3, self.GPIO.HIGH)
        self.GPIO.output(self.LEFT_IN4, self.GPIO.LOW)
        self.set_speed(speed)
        print("MotorController: Turning right.")

    def cleanup(self):
        self.stop()
        self.right_pwm.stop()
        self.left_pwm.stop()
        self.GPIO.cleanup()
        print("MotorController: Cleanup complete.")
