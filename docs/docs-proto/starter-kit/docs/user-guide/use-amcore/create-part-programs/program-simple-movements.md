# Program simple movements

In this section, you'll learn some basic EPPL concepts that allow you to create a program that performs some simple machine movements.

## Prerequisites

Before you continue with this tutorial, make sure:

* You can enable the machine
* You've set up the [motion constraints](../../configure-amcore/configure-machine-motion/configure-machine-motion.md)

> [!WARNING]
> Make sure your end effector has sufficient clearance (at least 50 mm) to run these programs without collision.

## Command a move

First, let's get an axis to perform a small movement. We'll go with a 10 mm straight line in the positive X-direction at a feedrate of 1000 mm/min:

```
metric
relative
linear x10 f1000
```

There's a little bit to unpack here.

* The metric statement causes AMCore to operate in metric units of measurement.
  * The default unit of measurement is metric and thus we can and will omit this statement from other examples.
* The relative statement causes any subsequent move to be relative to the current position (at the time of the move).
  * It's good practice to always specify that you're using either absolute or relative positions at the beginning of each program you write.
* linear sets the move mode to linear, causing the move to be a straight line.
* f1000 means "set the feedrate to 1000 mm/min".
* When using relative moves, x10 means "move the X-axis by 10 mm in the positive direction".

>[!NOTE]
> If you're familiar with G-codes, linear is the same as a G1 command, and relative is the same as a G91.

You can run the program now. You should see the program perform the move and then finish.

## Move back

Now, let's move back to where we started. Comment out the move and add a new line that does the opposite move:

```
relative
{ linear x10 f1000 }
linear x-10 f1000
```

Note the following:

* Lines surrounded by curly brackets in EPPL are comments and won't be executed.
* The X-axis command is now -10 mm, which moves it in the opposite (negative) direction.
  
Run the program and you should see the X-axis move back to it's starting position and then finish.

## Create a loop

Let's make it repeat these two moves indefinitely. Uncomment the first move and add a simple loop:

```
relative
n1
linear x10 f1000
linear x-10 f1000
goto n1
```

n1 is a label that you can jump to with the goto statement.

Before you run this program, note that it will run indefinitely. You'll need to abort the program (the main interface should have a button for this).

Aborting the program is likely to result in the machine not ending at the starting point, so you may need to readjust the position of the machine if you're working in a tight space.

## Control the loop

Now, let's make it repeat the movement each time we press the "r" key.

```
relative
n1
readkey(&key)
if key="r" then
    linear x10 f1000
    linear x-10 f1000
    sync
    goto n1
ifend
```

Note the following:

* The indentation is not required, but is recommended to improve readability.
* The readkey statement waits for you to press a key and assigns the key you press to a variable named key.
* The if statement checks the key you pressed - if you pressed "r", it will perform the moves and return to read another key.
* The sync statement ensures the moves are executed before continuing. Learn about "look-ahead" to understand this better.

Run this program. Each time you press the "r" key in the "Read/Write" window, the machine will repeat the small movement. If you press any other key, the program will exit.

## Next steps

This concludes this introduction to creating programs in AMCore. To continue learning, refer to the EPPL Guide.