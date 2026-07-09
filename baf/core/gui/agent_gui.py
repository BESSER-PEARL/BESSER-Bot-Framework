"""AgentGUI: BAF's interface to besser's GUIModel, with optional-dependency handling."""
from __future__ import annotations

import copy
import uuid

from baf.exceptions.logger import logger

try:
    from besser.BUML.metamodel.gui.graphical_ui import GUIModel, ViewContainer
    _BESSER_AVAILABLE = True
except ImportError:
    logger.warning(
        "besser GUI dependencies could not be imported. GUI features will be unavailable. "
        "Install with 'pip install --no-deps besser'."
    )
    GUIModel = None
    ViewContainer = None
    _BESSER_AVAILABLE = False


class AgentGUI:
    """BAF's interface to besser's :class:`GUIModel`, with helper methods for common GUI operations.

    Handles the case where besser is not installed: all methods log a warning and return
    ``None``/``False`` instead of raising an error. When besser *is* installed, attribute
    access is transparently delegated to the inner model so that existing code that uses
    ``gui.modules``, ``gui.name``, etc. continues to work unchanged.

    Args:
        model: the :class:`GUIModel` instance to wrap, or ``None``.
        gui_id: identifier for the AgentGUI.

    Attributes:
        _model: the inner :class:`GUIModel`, or ``None`` when besser is not installed or
            no model has been set.
        _id: identifier for the AgentGUI.
    """

    def __init__(self, model: GUIModel, gui_id: str | None = None):
        self._model: GUIModel = model
        if gui_id is None:
            gui_id = str(uuid.uuid4())
        self._id: str = gui_id

    # ------------------------------------------------------------------
    # Core proxy behaviour
    # ------------------------------------------------------------------

    @property
    def model(self):
        """The underlying GUIModel instance, or None."""
        return self._model

    @property
    def id(self) -> str:
        """Unique identifier for this GUI reply message."""
        return self._id

    def __getattr__(self, name: str):
        """Delegate attribute access to the inner GUIModel."""
        model = self._model
        if model is None:
            if not _BESSER_AVAILABLE:
                logger.warning(
                    f"Cannot access attribute '{name}': besser is not installed. "
                    "Install with 'pip install --no-deps besser'."
                )
            else:
                logger.warning(f"Cannot access attribute '{name}': no GUI model set.")
            return None
        return getattr(model, name)

    def __setattr__(self, name: str, value):
        """Delegate attribute assignment to the inner GUIModel for non-private names."""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        model = self._model
        if model is None:
            logger.warning(f"Cannot set attribute '{name}': no GUI model set.")
            return
        setattr(model, name, value)

    def __bool__(self) -> bool:
        return self._model is not None

    # ------------------------------------------------------------------
    # Helper: deep copy
    # ------------------------------------------------------------------

    def deep_copy(self) -> 'AgentGUI':
        """Return a deep copy of this :class:`AgentGUI` and its inner model.

        Returns:
            AgentGUI: a new instance wrapping a deep-copied model.
        """
        model = self._model
        if model is None:
            return AgentGUI(None)
        try:
            return AgentGUI(copy.deepcopy(model))
        except Exception as e:
            logger.warning(f"Could not deep-copy GUI model: {e}. Returning a shallow reference.")
            return AgentGUI(model)

    # ------------------------------------------------------------------
    # Helper: find
    # ------------------------------------------------------------------

    def find_component_by_id(self, component_id: str):
        """Find a component anywhere in the model by its ``component_id``.

        Recursively searches through all modules → screens → containers.

        Args:
            component_id (str): the ``component_id`` to look for.

        Returns:
            The matching :class:`ViewElement`, or ``None`` if not found.
        """
        model: GUIModel = self._model
        if model is None:
            logger.warning("Cannot find component: no GUI model set.")
            return None
        for module in model.modules:
            for screen in module.screens:
                result = self._find_in_elements(screen.view_elements, component_id)
                if result is not None:
                    return result
        return None

    def _find_in_elements(self, elements, component_id: str):
        """Recursively search *elements* for a matching ``component_id``."""
        for el in elements:
            if getattr(el, 'component_id', None) == component_id:
                return el
            child_elements = getattr(el, 'view_elements', None)
            if child_elements:
                found = self._find_in_elements(child_elements, component_id)
                if found is not None:
                    return found
        return None

    # ------------------------------------------------------------------
    # Helper: update
    # ------------------------------------------------------------------

    def update_component_by_id(self, component_id: str, **kwargs):
        """Update attributes of a component located by its ``component_id``.

        Args:
            component_id (str): identifies the component to update.
            **kwargs: attribute names and their new values.

        Returns:
            The updated component if found, or ``None``.
        """
        model = self._model
        if model is None:
            logger.warning("Cannot update component: no GUI model set.")
            return None
        component = self.find_component_by_id(component_id)
        if component is None:
            logger.warning(f"Component with id '{component_id}' not found in GUI model.")
            return None
        for attr, value in kwargs.items():
            setattr(component, attr, value)
        return component

    # ------------------------------------------------------------------
    # Helper: add
    # ------------------------------------------------------------------

    def add_component(self, component, parent_id: str = None, screen_name: str = None) -> bool:
        """Add a component to the GUI model.

        Resolution order:

        1. If *parent_id* is given, the component is added to the container that has
           that ``component_id`` (must be a container with ``view_elements``).
        2. If *screen_name* is given, the component is added to the top-level
           ``view_elements`` of the named screen.
        3. Otherwise the component is added to the main screen (``is_main_page=True``),
           or to the first screen when no main screen exists.

        Args:
            component: the :class:`ViewElement` to add.
            parent_id (str | None): ``component_id`` of the target container.
            screen_name (str | None): name of the target screen (used when *parent_id* is
                not given).

        Returns:
            bool: ``True`` if the component was added, ``False`` otherwise.
        """
        model = self._model
        if model is None:
            logger.warning("Cannot add component: no GUI model set.")
            return False

        if parent_id is not None:
            parent = self.find_component_by_id(parent_id)
            if parent is None:
                logger.warning(f"Parent container with id '{parent_id}' not found.")
                return False
            if not hasattr(parent, 'view_elements'):
                logger.warning(f"Component '{parent_id}' is not a container (no view_elements).")
                return False
            parent.view_elements = parent.view_elements | {component}
            return True

        target = self.get_screen(screen_name)
        if target is None:
            logger.warning("No screen found to add the component to.")
            return False
        target.view_elements = target.view_elements | {component}
        return True

    # ------------------------------------------------------------------
    # Helper: screens
    # ------------------------------------------------------------------

    def get_screen(self, screen_name: str = None):
        """Retrieve a screen by name, or the main screen when no name is given.

        Falls back to the first screen when there is no screen marked as main.

        Args:
            screen_name (str | None): the screen name to look for, or ``None`` to get
                the main/first screen.

        Returns:
            The :class:`Screen`, or ``None`` if not found.
        """
        model = self._model
        if model is None:
            logger.warning("Cannot get screen: no GUI model set.")
            return None

        first = None
        for module in model.modules:
            for screen in module.screens:
                if first is None:
                    first = screen
                if screen_name is not None:
                    if screen.name == screen_name:
                        return screen
                elif getattr(screen, 'is_main_page', False):
                    return screen

        # Fallbacks
        if screen_name is None:
            return first
        return None
