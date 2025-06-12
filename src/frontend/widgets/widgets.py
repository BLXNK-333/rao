from typing import Optional, Any, Set, Dict, List, TYPE_CHECKING, Callable
import time

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    class _WindowProto(tk.Misc, tk.BaseWidget): ...
else:
    _WindowProto = object


class BaseWindow(_WindowProto):
    """
    Mixin to center a Tk or Toplevel window on the screen.

    Provides the show_centered() method, which sets the window size and
    positions it centered. If size is not provided, falls back to
    self._last_geometry or defaults to two-thirds of the screen.
    """

    def show_centered(self, geometry: str | None = None):
        """
        Centers the window on the screen and shows it.

        Args:
            geometry (str | None): Geometry string like 'WIDTHxHEIGHT', e.g. '500x400'.
                                  If None, uses self._last_geometry or defaults to
                                  two-thirds of the screen size.
        """
        self.update_idletasks()
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()

        if geometry is None:
            width = scr_w * 2 // 3
            height = scr_h * 2 // 3
        else:
            width, height = map(int, geometry.split("+")[0].split("x"))

        x = (scr_w - width) // 2
        y = (scr_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()


class ScrolledFrame(ttk.Frame):
    """
    A scrollable frame widget built on top of ttk.Frame and tk.Canvas.

    This widget creates a canvas with a vertical scrollbar, and embeds a child
    frame (`self.content`) inside the canvas. Content added to `self.content` will
    be scrollable vertically. Automatically hides the scrollbar when it's not needed.

    You can use either `.pack()` or `.grid()` to place the `ScrolledFrame` in its parent.

    Usage examples:
        # Using pack
        frame = ScrolledFrame(parent)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame.content, text="Scrollable content here").pack()
        frame.bind_scroll_events()

        # Using grid
        frame = ScrolledFrame(parent)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame.content, text="Scrollable content here").grid()
        frame.bind_scroll_events()
    """

    def __init__(self, parent: tk.Misc, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent, *args, **kwargs)

        # Canvas for scrolling
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Frame to hold content
        self.content = ttk.Frame(self._canvas)
        self._window_id = self._canvas.create_window((0, 0), window=self.content, anchor="nw")

        # Grid stretch configuration
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Bind canvas and content resizing
        self._canvas.bind("<Configure>", self._adjust_canvas)
        self.content.bind("<Configure>", self._update_scrollregion)

    def _adjust_canvas(self, event: Optional[tk.Event] = None) -> None:
        """
        Adjusts the embedded content frame to match the canvas width
        and updates the scrollregion.
        """
        canvas_width = self._canvas.winfo_width()
        self._canvas.itemconfig(self._window_id, width=canvas_width)
        self._update_scrollregion()

    def _update_scrollregion(self, event: Optional[tk.Event] = None) -> None:
        """
        Updates the scrollregion of the canvas and toggles the scrollbar
        visibility based on the content height.
        """
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        if self._is_scrollbar_needed():
            self._scrollbar.grid()
        else:
            self._scrollbar.grid_remove()

    def _is_scrollbar_needed(self) -> bool:
        """
        Returns True if the content is taller than the canvas,
        meaning the scrollbar is needed.
        """
        return self._canvas.winfo_height() < self.content.winfo_reqheight()

    def _on_scroll(self, event: tk.Event) -> Optional[str]:
        """
        Generic cross-platform mouse scroll handler.

        Supports Windows/macOS (MouseWheel) and Linux/X11 (Button-4/5).
        """
        if not self._is_scrollbar_needed():
            return "break"

        if event.delta:  # Windows/macOS
            direction = -1 if event.delta > 0 else 1
        elif hasattr(event, "num") and event.num in (4, 5):  # Linux
            direction = -1 if event.num == 4 else 1
        else:
            direction = 0

        self._canvas.yview_scroll(direction, "units")
        return "break"

    def bind_scroll_events(
            self,
            widget: Optional[tk.Widget] = None,
            bound_widgets: Optional[Set[tk.Widget]] = None
    ) -> None:
        """
        Recursively binds scroll events to all child widgets to ensure
        consistent scrolling behavior.

        Args:
            widget: The widget to start binding from (defaults to self).
            bound_widgets: Internal set to prevent duplicate bindings.
        """
        if widget is None:
            widget = self
        if bound_widgets is None:
            bound_widgets = set()

        if widget not in bound_widgets:
            widget.bind("<MouseWheel>", self._on_scroll)
            widget.bind("<Button-4>", self._on_scroll)
            widget.bind("<Button-5>", self._on_scroll)
            bound_widgets.add(widget)

        for child in widget.winfo_children():
            self.bind_scroll_events(child, bound_widgets)


class UndoEntry(ttk.Entry):
    """
    A custom Entry widget with undo/redo functionality.

    Supports:
    - Undo (Ctrl+Z) and redo (Ctrl+Y) for text changes.

    Args:
        master (Optional[tk.Misc]): Parent widget.
        delay_ms (int): Delay in milliseconds between changes for undo detection.
        **kwargs: Additional arguments passed to `ttk.Entry`.

    Usage:
        entry = UndoEntry(root, delay_ms=500)
        entry.pack()
    """

    def __init__(
            self,
            master: Optional[tk.Misc] = None,
            delay_ms: int = 500,
            **kwargs: Any
    ) -> None:
        """
        Initializes the UndoEntry widget with undo/redo functionality.

        Args:
            master (Optional[tk.Misc]): Parent widget.
            delay_ms (int): Debounce delay in milliseconds for undo operations.
            **kwargs: Additional arguments passed to the `ttk.Entry` constructor.
        """
        self._var: Optional[tk.StringVar] = kwargs.pop("textvariable", None)
        if self._var is None:
            self._var = tk.StringVar()

        super().__init__(master, textvariable=self._var, **kwargs)

        self._undo_stack: list[str] = []
        self._redo_stack: list[str] = []
        self._last_change_time: float = 0
        self._delay: float = delay_ms / 1000
        self._ignore: bool = False

        self._initial_value = self._var.get()
        self._undo_stack.append(self._initial_value)

        self._var.trace_add("write", self._on_write)
        self.bind("<Control-z>", self._undo)
        self.bind("<Control-y>", self._redo)

    def _on_write(self, *args: Any) -> None:
        """
        Handles text changes and adds the new value to the undo stack.

        Args:
            *args: Additional arguments passed from the trace callback.
        """
        if self._ignore:
            return

        now = time.time()
        current_value = self._var.get()

        if not self._undo_stack or now - self._last_change_time > self._delay:
            if current_value != self._undo_stack[-1]:
                self._undo_stack.append(current_value)
                self._last_change_time = now
                self._redo_stack.clear()
        else:
            self._undo_stack[-1] = current_value

    def _undo(self, event: Optional[tk.Event] = None) -> str:
        """
        Performs the undo operation by restoring the previous state from the undo stack.
        Returns "break" to prevent default event handling.
        """
        if len(self._undo_stack) > 1:
            self._redo_stack.append(self._undo_stack.pop())
            self._ignore = True
            self._var.set(self._undo_stack[-1])
            self.icursor("end")
            self._ignore = False
            self._last_change_time = time.time()
        return "break"

    def _redo(self, event: Optional[tk.Event] = None) -> str:
        """
        Performs the redo operation by reapplying the text from the redo stack.
        Returns "break" to prevent default event handling.
        """
        if self._redo_stack:
            value = self._redo_stack.pop()
            self._undo_stack.append(value)
            self._ignore = True
            self._var.set(value)
            self.icursor("end")
            self._ignore = False
            self._last_change_time = time.time()
        return "break"


class UndoText(tk.Text):
    """
    A custom Text widget with basic undo/redo functionality and optional auto-resizing.

    Supports:
    - Undo (Ctrl+Z) and redo (Ctrl+Y) for text changes.
    - Auto-growing height based on content if `resize=True`.
    - Optional styling via `styles_dict`.

    Args:
        master (Optional[tk.Misc]): Parent widget.
        initial_value (str): Initial text content.
        delay_ms (int): Debounce delay in milliseconds for registering undo states.
        resize (bool): Whether to auto-adjust height based on content.
        styles_dict (Optional[Dict[str, Any]]): Dictionary of widget styles.
        **kwargs: Additional arguments passed to `tk.Text`.

    Usage:
        text = UndoText(root, initial_value="Hello", resize=True)
        text.pack()
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        initial_value: str = "",
        delay_ms: int = 500,
        resize: bool = False,
        styles_dict: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the UndoText widget.
        """
        super().__init__(master, **kwargs)

        if styles_dict:
            self.config(**styles_dict)

        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []
        self._last_change_time: float = 0
        self._delay: float = delay_ms / 1000
        self._ignore: bool = False
        self._resize_enabled: bool = resize

        self.insert("1.0", initial_value)
        self._undo_stack.append(initial_value)

        self.bind("<KeyRelease>", self._on_write)
        self.bind("<Control-z>", self._undo)
        self.bind("<Control-y>", self._redo)

        if self._resize_enabled:
            self._enable_resize()

    def _on_write(self, event: Optional[tk.Event] = None) -> None:
        """
        Handles text changes, adds new state to undo stack if needed,
        and updates widget height if resize is enabled.
        """
        if self._ignore:
            return

        now = time.time()
        current_value = self.get("1.0", "end-1c")

        if not self._undo_stack or now - self._last_change_time > self._delay:
            if current_value != self._undo_stack[-1]:
                self._undo_stack.append(current_value)
                self._last_change_time = now
                self._redo_stack.clear()
        else:
            self._undo_stack[-1] = current_value

        if self._resize_enabled:
            self._resize(event)

    def _undo(self, event: Optional[tk.Event] = None) -> str:
        """
        Performs undo operation by restoring previous state from undo stack.
        Returns "break" to prevent default event behavior.
        """
        if len(self._undo_stack) > 1:
            self._redo_stack.append(self._undo_stack.pop())
            self._ignore = True
            self._set_text(self._undo_stack[-1])
            self._ignore = False
            self._last_change_time = time.time()
        return "break"

    def _redo(self, event: Optional[tk.Event] = None) -> str:
        """
        Performs redo operation by reapplying text from redo stack.
        Returns "break" to prevent default event behavior.
        """
        if self._redo_stack:
            text = self._redo_stack.pop()
            self._undo_stack.append(text)
            self._ignore = True
            self._set_text(text)
            self._ignore = False
            self._last_change_time = time.time()
        return "break"

    def _set_text(self, content: str) -> None:
        """
        Sets the text content of the widget while preserving cursor position.

        Args:
            content (str): New text to display.
        """
        cursor = self.index("insert")
        self.delete("1.0", "end")
        self.insert("1.0", content)
        try:
            self.mark_set("insert", cursor)
        except tk.TclError:
            pass

    def _enable_resize(self) -> None:
        """
        Enables automatic height adjustment based on content.
        """
        self.bind("<Configure>", self._resize)
        self.after(100, self._resize)

    def _resize(self, event: Optional[tk.Event] = None) -> None:
        """
        Adjusts the height of the widget based on the number of visible lines.
        """
        self.update_idletasks()
        try:
            num_lines = self.count("1.0", "end", "displaylines")[0]
            self.config(height=max(1, num_lines))
        except Exception:
            pass


class HoverButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        self.default_bg = kwargs.pop("background", "#eff0f1")
        self.hover_bg = kwargs.pop("activebackground", "#e7e7e7")

        super().__init__(
            master,
            background=self.default_bg,
            activebackground=self.hover_bg,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            **kwargs
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self.configure(background=self.hover_bg)

    def _on_leave(self, event):
        self.configure(background=self.default_bg)


class ToggleButton(HoverButton):
    """
    A custom toggle button that switches between two images (on/off state).
    Optionally accepts a callback function (passed as 'command' in kwargs)
    to execute when the button is toggled.
    """

    def __init__(
            self,
            master: tk.Misc = None,
            image_on: tk.PhotoImage = None,
            image_off: tk.PhotoImage = None,
            initial_state: bool = False,
            **kwargs
    ):
        """
        Initializes the toggle button.

        Args:
            master: The parent widget for the button.
            image_on: The image for the "on" state.
            image_off: The image for the "off" state.
            initial_state: The initial state of the button (True for "on", False for "off").
            **kwargs: Additional keyword arguments passed to the Button constructor.
                      The 'command' key (if present) will be used as a callback function
                      when the button is toggled.
        """
        callback = kwargs.pop('command', None)
        super().__init__(master, **kwargs)

        self._image_on = image_on
        self._image_off = image_off
        self._is_on = initial_state
        self._callback: Optional[Callable[[], None]] = callback

        self.configure(image=self._image_on if self._is_on else self._image_off)
        self.configure(command=self._on_click)

    def _on_click(self):
        """
        Handles the button click event. Toggles the button's state
        and calls the callback function (if provided).
        """
        self.toggle()
        if self._callback:
            self._callback()

    def toggle(self):
        """
        Toggles the button's state between "on" and "off", updating the button's image.
        """
        self._is_on = not self._is_on
        self._update_image()

    def turn_on(self):
        """
        Sets the button's state to "on" and updates the image accordingly.
        """
        if not self._is_on:
            self._is_on = True
            self._update_image()

    def turn_off(self):
        """
        Sets the button's state to "off" and updates the image accordingly.
        """
        if self._is_on:
            self._is_on = False
            self._update_image()

    def _update_image(self):
        """
        Updates the button's image based on the current state ("on" or "off").
        """
        image = self._image_on if self._is_on else self._image_off
        self.configure(image=image)

    @property
    def state(self):
        return self._is_on
