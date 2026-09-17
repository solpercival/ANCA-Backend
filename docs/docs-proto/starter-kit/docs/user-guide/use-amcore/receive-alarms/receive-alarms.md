# Receive alarms

## Understanding the alarm system

The alarm system follows an event-based architecture. Client processes can receive alarm events by subscribing to the alarm system. Clients can also unsubscribe when they don't need to receive alarms anymore.

Clients that subscribe after the alarm system has been online for a period of time can synchronize currently retained alarms by initiating an alarm refresh routine.

The alarm system has three types of events:

* **Alarm raised event**: occurs when a new alarm instance is raised.
* **Alarm changed event**: occurs when the state of an alarm instance has changed (such as being acknowledged or confirmed).
* **Message event**: occurs when a message is published. 

> [!NOTE]
> Refer to the SDK documentation for more details.

## Building a client of the alarm system

The event-based architecture decouples clients from the alarm system, enabling users to build their own UI and event sinks that display process alarms with varying levels of granularity.

### Event sink example

Suppose that you want to trigger a data log every time that an alarm event with `Error` or `Fatal` severity level is raised. Follow the steps below to achieve this.

1. Subscribe your application to the alarm system.
2. Periodically query for alarm events.
3. Check the type and severity level of the received event.
4. Run the application logic if the alarm severity level satisfies your condition.

For a more detailed step-by-step tutorial, see [Build your first event sink](./build-your-first-event-sink.md#build-your-first-event-sink) .

## Receiving alarms in your preferred locales

To receive alarms in your preferred locales, include a list of locale names in your alarm subscription. The alarm system will publish an alarm event for each subscribed locale. 

You can also change the subscribed locales at any time by resubscribing.

## Receiving alarms from the OPC-UA server

The OPC-UA server supports the [Alarm and Condition Server Facet](https://profiles.opcfoundation.org/profile/1754), enabling OPC-UA clients to receive and interact with alarms remotely.

You can submit a list of preferred locales to the OPC-UA server upon activating a session and alarm events will be published in the highest-ranked locale in that list.