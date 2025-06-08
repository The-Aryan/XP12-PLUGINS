# Best Practices for X-Plane Plugin Development using XPPython3

**Author:** Aryan Shukla
**Plugin Reference:** Generate FDR Files Plugin
**Tools Used:** XPPython3 SDK, Python 3.x

---

## ὐ Plugin Architecture

### ✅ Use the XPPython3 Plugin Lifecycle Properly:

* Follow the X-Plane plugin lifecycle: `XPluginStart`, `XPluginEnable`, `XPluginDisable`, `XPluginStop`.
* Keep these functions minimal and delegate core logic to class methods.

### ✅ Isolate Logic:

Encapsulate functionality like `StartLogging`, `StopLogging`, etc., to keep lifecycle functions clean and modular.

---

## 📋 Menu and User Control

### ✅ Create Clear Menu Interfaces:

Use X-Plane’s menu APIs:

```python
self.menuId = xp.createMenu("genFDR", None, 0, self.ToggleLogging, 0)
self.menuIndex = xp.appendMenuItem(self.menuId, "Toggle: ON", 1, 1)
```

### ✅ Manage Plugin State:

Use a single boolean (`self.isLogging`) to track state and update menu text accordingly.

---

## 🛫 Flight Loop and Draw Callbacks

### ✅ Register Callbacks Safely:

```python
xp.registerFlightLoopCallback(self.FlightLoopCallback, self.sampling_rate, 0)
```

* Register once.
* Avoid multiple registrations without corresponding unregistration.

### ✅ Always Unregister Cleanly:

Use exact parameters while unregistering:

```python
xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
```

### ⛔️ Avoid Duplicate Registration:

Improper unregistration causes errors like:
`ValueError: Unknown flight loop callback`

---

## 💾 Logging and File Handling

### ✅ Use Timestamps for File Naming:

```python
time = datetime.datetime.now().strftime('%H-%M-%S')
date = datetime.datetime.now().strftime('%d-%m-%Y')
```

Ensure unique and traceable file names.

### ✅ Flush Regularly:

```python
self.file.flush()
```

Prevents data loss on crash or early shutdown.

---

## 📊 DataRefs and Sampling

### ✅ Use a Dictionary for DataRefs:

```python
self.datarefs = {
    'longitude': 'sim/flightmodel/position/longitude',
    # ...
}
```

Register pointers only once:

```python
self.datarefs_pointers = {k: xp.findDataRef(v) for k, v in self.datarefs.items()}
```

### ✅ Handle Missing DataRefs:

```python
val = xp.getDataf(ref) if ref else float('nan')
```

Don’t assume all DataRefs are present (especially with third-party aircraft).

---

## 🚒 Error Handling and Debugging

### ✅ Use xp.log():

```python
xp.log("Flight Loop Callback triggered")
```

Treat it like a debug print. Helps with in-sim troubleshooting.

### ✅ Isolate Callback Errors:

```python
try:
    # logic
except Exception as e:
    xp.log(f"[Error] FlightLoopCallback: {e}")
```

Avoid crashes inside callbacks.

---

## 🪯 Cleanup and Exit Strategy

### ✅ Always Close Files:

```python
if self.file:
    self.file.close()
    self.file = None
```

Avoid file locks and corruption.

### ✅ Unregister All Callbacks:

```python
xp.unregisterDrawCallback(...)
xp.unregisterFlightLoopCallback(...)
```

Prevents orphaned references and X-Plane log spam.

---

## 🚀 Extra Ideas for Future Improvements

| Feature               | Description                              |
| --------------------- | ---------------------------------------- |
| Configurable DataRefs | Let user choose which datarefs to log.   |
| Sampling Rate Control | Allow real-time change in logging rate.  |
| UI Panel              | Provide GUI (imgui or native window)     |
| Log Rotation          | Split logs per session or flight phase   |
| Aircraft Detection    | Auto-detect loaded aircraft, tail number |

---

*This guide is based on hands-on development and debugging experience during the creation of the Generate FDR Files plugin. When in doubt, log more, crash less, and always unregister what you register.*
