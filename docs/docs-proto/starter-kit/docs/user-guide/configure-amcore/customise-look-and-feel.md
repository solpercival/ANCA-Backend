# Customize look and feel

Some aspects of AMCore's appearance can be customised. This section lists each aspect and provides instructions to modify it.

## Splash screen

The splash screen is the image that is displayed when AMCore is starting. You can change it by providing your own image.

To change the splash screen image:

1. Create a bitmap image file of the splash screen you would like. It must be 460 pixels wide, and 345 pixels high
2. Name the file `splash.bmp` and place it in a folder named `img` in the home folder.

## Service icon

The service icon is the image that is displayed in the service prompt (before the splash screen) when AMCore is starting. You can change it by providing your own image.

To change the service icon:

1. Create a bitmap image file of the service icon you would like. It must be 55 pixels wide, and 16 pixels high
2. Name the file `splash_service.bmp` and place it in a folder named `img` in the home folder.

## Axis image

The axis image is the image that appears in the status tool to help the end user understand the axis arrangement of the machine. You can change it by providing your own image.

> [!NOTE]
> The status tool is not visible by default.

To change the axis image:

1. Create a bitmap image file of the axis image you would like. It must be 500 pixels wide, and 370 pixels high
2. Name the file `status_axes.bmp` and place it in a folder named `img` in the home folder.

## Menu logo

The menu logo is the image that appears at the top of the ANCA Menu. You can change it by providing your own image.

> [!NOTE]
> The ANCA Menu (and the menu logo) is not visible by default.

To change the menu logo:

1. Create a bitmap image file of the menu logo you would like. It must be 55 pixels wide, and 16 pixels high
2. Name the file `menu_logo.bmp` and place it in a folder named `img` in the home folder.

## Alarm dialogs

Alarm dialogs can be disabled by setting the configuration property `user_interface.alarm_dialogs.enable` to `False`.

To develop a custom dialog for alarms, see [Build your first event sink](../use-amcore/receive-alarms/build-your-first-event-sink.md#build-your-first-event-sink).