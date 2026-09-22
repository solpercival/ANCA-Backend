# Write your first program

In this example, we'll use the Active Program Display (APD) to activate and run a simple "Hello World" program in two ways.

## Quickly run "Hello World!"

First, let's quickly get a program running using Manual Data Input (MDI).

1. In APD, click **MDI** in the menu bar.
2. Enter the following code:
    ```
    write("Hello World!")
    dwell x5
    ```
 3. Click **Activate**.
 4. Use your main interface to run the program by clicking **Cycle Start**.

The "Hello World" program will now run. It should display a "Read/Write" window that reads "Hello World!". After 5 seconds, the program should finish, which closes the window.

Now, the next time you open MDI, you can press **Recall** to quickly bring up and modify the previous code you wrote.

Keep in mind that MDI is only intended as a quick way to test some code - the code you write won't be saved! Let's look at a better way to write programs.

## Save and run "Hello World!"

Part programs are simply text files written in EPPL. So, to create and run a program:

1. Open your favourite text editor.
2. Enter the following text:
    ```
    write("Hello World!")
    dwell x5
    ```
   Make sure you end the program with an empty line.
3. Save the file using a .pp file extension.
4. In APD, click **Program &rarr; Activate**.
5. Select the file you saved in Step 1, then click **Open**.
6. Use your main interface to run the program by clicking **Cycle Start**.

This time, after the program runs, the program remains activated. Clicking **Cycle Start** again will run it again. You can deactivate it by clicking **Program &rarr; Deactivate**.

This method also lets you keep the program for later use. Much better!