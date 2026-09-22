# Build your first event sink

In this tutorial, you will learn how to create a basic alarm event sink using the CNCC Alarm API. This event sink specifically focuses on capturing alarm raised events of the Error and Fatal severity levels.

## Subscribing to the alarm system

First, you need to subscribe to the alarm system, and for that you need to provide the following information:

* The locale(s) in which you want to receive events.
* The subscription option. In this tutorial we will use "None".
* The source location i.e. the location in your program where the subscription is initiated.
* Finally, the subscription handle that you'll need to receive events.

```c
CnccAlarmSubscription subscription_;
auto locales = "en,de" // receive events in English and German
auto option = CNCCALARMSUBSCRIPTIONOPTION_NONE;
auto result = CnccAlarmSubscribe(
    &subscription_, 
    locales,
    option,
    CNCC_CURRENT_SOURCE_LOCATION);
  
if (result != CNCCRESULT_OK) {
    printf("Failed to subscribe to Alarm Controller: %d", result);
}
```

## Receiving alarm events

Once the subscription has been successfully initiated, use the subscription handle to query for events. After running your event sink logic, free the memory of the event.

```c
auto interval = INFINITE;
while (1) {
    CnccAlarmEventType event_type;
    auto result = CnccAlarmGetEvent(subscription_, &event, interval);
    if (result != CNCCRESULT_OK) {
        printf("Receive error: %d\n", result);
        continue;
    }
    
    // Handle the event here
    
    CnccAlarmFreeEvent(&event);
}
```

You need to determine the event type and decide whether it is relevant:

```c
result = CnccAlarmEventGetType(event, &event_type);
if (result != CNCCRESULT_OK) {
    printf("CnccAlarmEventGetType error: %d\n", result);
    CnccAlarmFreeEvent(&event);
    continue;
}

switch (event_type) {
    case CNCCALARMEVENTTYPE_ALARM_INSTANCE_RAISED:
        ProcessAlarmEvent(event);
        break;
    default:
        // Ignore other event types
        break;
}
```

In `ProcessAlarmEvent`, you can use the event handle to query the alarm instance data you need, such as severity level or event locale, and run other application logic.

If you no longer want to get alarm events, issue an unsubscribe request to the alarm system which will also invalidate the subscription handle:

```c
CnccAlarmUnsubscribe(&subscription_, CNCC_CURRENT_SOURCE_LOCATION);
```

## Next steps

To learn more about the alarm system functionalities and behavior, refer to the CNCC API Documentation.