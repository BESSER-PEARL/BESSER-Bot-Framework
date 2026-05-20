import asyncio
import importlib
import inspect
import json
import operator
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, get_type_hints

import yaml

from baf.core.transition.event import Event
from baf.core.message import Message, MessageType
from baf.core.entity.entity import Entity
from baf.core.intent.intent import Intent
from baf.core.intent.intent_parameter import IntentParameter
from baf.core.property import Property
from baf.core.processors.processor import Processor
from baf.core.session import Session
from baf.core.state import State
from baf.core.transition.transition import Transition
from baf.db import DB_MONITORING
from baf.db.db_handler import DBHandler
from baf.db.monitoring_db import MonitoringDB
from baf.exceptions.exceptions import AgentNotTrainedError, DuplicatedEntityError, DuplicatedInitialStateError, \
    DuplicatedIntentError, DuplicatedStateError, InitialStateNotFound
from baf.exceptions.logger import logger
from baf.library.transition.events.base_events import ReceiveMessageEvent, ReceiveJSONEvent, ReceiveFileEvent
from baf.nlp.intent_classifier.intent_classifier_configuration import IntentClassifierConfiguration, \
    SimpleIntentClassifierConfiguration
from baf.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from baf.nlp.nlp_engine import NLPEngine
from baf.platforms.platform import Platform
from baf.platforms.telegram.telegram_platform import TelegramPlatform
from baf.platforms.websocket.websocket_platform import WebSocketPlatform
from baf.platforms.github.github_platform import GitHubPlatform
from baf.platforms.gitlab.gitlab_platform import GitLabPlatform
from baf.platforms.a2a.a2a_platform import A2APlatform
from baf.reasoning import Tool, Skill, Workspace


class Agent:
    """The agent class.

    Args:
        name (str): The agent's name
        persist_sessions (bool): whether to persist sessions or not after restarting the agent

    Attributes:
        _name (str): The agent name
        _persist_sessions (bool): whether to persist sessions or not after restarting the agent
        _platforms (list[Platform]): The agent platforms
        _platforms_threads (list[threading.Thread]): The threads where the platforms are run
        _event_loop (asyncio.AbstractEventLoop): The event loop managing external events
        _event_thread (threading.Thread): The thread where the event loop is run
        _nlp_engine (NLPEngine): The agent NLP engine
        _config (dict[str, Any]): The agent configuration parameters
        _default_ic_config (IntentClassifierConfiguration): the intent classifier configuration used by default for the
            agent states
        _sessions (dict[str, Session]): The agent sessions
        _trained (bool): Whether the agent has been trained or not. It must be trained before it starts its execution.
        _monitoring_db (MonitoringDB): The monitoring component of the agent that communicates with a database to store
            usage information for later visualization or analysis
        states (list[State]): The agent states
        intents (list[Intent]): The agent intents
        entities (list[Entity]): The agent entities
        global_initial_states (list[State, Intent]): List of tuples of initial global states and their triggering intent
        global_state_component (dict[State, list[State]]): Dictionary of global state components, where key is initial
            global state and values is set of states in corresponding global component
        processors (list[Processors]): List of processors used by the agent
        _tools (dict[str, Tool]): Tools registered on the agent and exposed
            to the predefined reasoning state. Keyed by tool name. Populated
            by :meth:`add_tool` / :meth:`new_tool` / :meth:`load_tools`, the
            ``@agent.tool`` decorator, and indirectly by :meth:`add_workspace`
            / :meth:`new_workspace` (which register the universal
            ``list_directory`` / ``read_file`` and — when at least one
            workspace is writable — ``write_file`` / ``create_file`` /
            ``delete_file`` tools).
        _skills (dict[str, Skill]): Markdown-based playbooks the reasoning
            state injects into the system prompt. Keyed by skill name.
            Populated by :meth:`add_skill` / :meth:`new_skill` /
            :meth:`load_skills`.
        _workspaces (dict[str, Workspace]): Filesystem workspaces the agent
            can browse and (when ``writable=True``) modify through the
            universal workspace tools. Keyed by workspace name. Populated
            by :meth:`add_workspace` / :meth:`new_workspace`.
    """

    def __init__(
            self,
            name: str,
            persist_sessions: bool = False,
            user_profiles_path: str | None = None,
            agent_configurations_path: str | None = None,
    ):
        self._name: str = name
        self._persist_sessions: bool = persist_sessions
        self._platforms: list[Platform] = []
        self._platforms_threads: list[threading.Thread] = []
        self._nlp_engine = NLPEngine(self)
        self._config: dict[str, Any] = {}
        self._default_ic_config: IntentClassifierConfiguration = SimpleIntentClassifierConfiguration()
        self._sessions: dict[str, Session] = {}
        self._trained: bool = False
        self._monitoring_db: MonitoringDB = None
        self._db_handler: DBHandler | None = None
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []
        self.global_initial_states: list[tuple[State, Intent]] = []
        self.global_state_component: dict[State, list[State]] = dict()
        self.processors: list[Processor] = []
        self._user_profiles: Any = None
        self._agent_configurations: dict[str, Any] = {}
        self._tools: dict[str, Tool] = {}
        self._skills: dict[str, Skill] = {}
        self._workspaces: dict[str, Workspace] = {}

        if user_profiles_path:
            self.load_user_profiles(user_profiles_path)

        if agent_configurations_path:
            self.load_agent_configurations(agent_configurations_path)

    @property
    def name(self):
        """str: The agent name."""
        return self._name

    @property
    def nlp_engine(self):
        """NLPEngine: The agent NLP engine."""
        return self._nlp_engine

    @property
    def config(self):
        """dict[str, Any]: The agent configuration parameters."""
        return self._config

    def load_properties(self, path: str) -> None:
        """Read a properties file and store its properties in the agent configuration.

        Supported formats are YAML (``.yaml``, ``.yml``).

        See ``baf/test/examples/config.yaml`` in the repository for a complete
        example of an agent configuration file.

        Args:
            path (str): the path to the properties file
        """
        suffix = Path(path).suffix.lower()
        if suffix not in {'.yaml', '.yml'}:
            raise ValueError('Only YAML configuration files are supported (.yaml, .yml)')

        with open(path, encoding='utf-8') as config_file:
            loaded_config = yaml.safe_load(config_file) or {}
        if not isinstance(loaded_config, dict):
            raise ValueError('YAML properties file must contain a mapping at the root level')
        self._flatten_yaml_properties(loaded_config)

    def _flatten_yaml_properties(self, data: Any, prefix: str = '') -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                next_prefix = f'{prefix}.{key}' if prefix else str(key)
                self._flatten_yaml_properties(value, next_prefix)
            return

        if isinstance(data, list):
            if prefix:
                self._config[prefix] = data
            for index, item in enumerate(data):
                if isinstance(item, dict) and len(item) == 1:
                    item_key, item_value = next(iter(item.items()))
                    next_prefix = f'{prefix}.{item_key}' if prefix else str(item_key)
                    self._flatten_yaml_properties(item_value, next_prefix)
                else:
                    next_prefix = f'{prefix}.{index}' if prefix else str(index)
                    self._flatten_yaml_properties(item, next_prefix)
            return

        if prefix:
            self._config[prefix] = data

    @staticmethod
    def _coerce_property_value(value: Any, target_type: type) -> Any:
        if isinstance(value, target_type):
            return value

        if target_type is bool:
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {'true', '1', 'yes', 'y', 'on'}:
                    return True
                if normalized in {'false', '0', 'no', 'n', 'off'}:
                    return False
                raise ValueError(f'Cannot parse boolean value from {value!r}')
            if isinstance(value, (int, float)):
                return bool(value)

        if target_type in {str, int, float}:
            return target_type(value)

        return value

    def get_property(self, prop: Property) -> Any:
        """Get an agent property's value

        Args:
            prop (Property): the property to get its value

        Returns:
            Any: the property value, or None
        """
        value = self._config.get(prop.name)

        if value is None:
            return prop.default_value

        try:
            return self._coerce_property_value(value, prop.type)
        except (TypeError, ValueError):
            logger.warning(
                "Could not cast property '%s' value %r to %s. Using default value %r",
                prop.name,
                value,
                prop.type,
                prop.default_value,
            )
            return prop.default_value

    def set_property(self, prop: Property, value: Any):
        """Set an agent property.

        Args:
            prop (Property): the property to set
            value (Any): the property value
        """
        if (value is not None) and (not isinstance(value, prop.type)):
            raise TypeError(f"Attempting to set the agent property '{prop.name}' with a "
                            f"{type(value)} value: {value}. The expected property value type is {prop.type}")
        self._config[prop.name] = value

    @property
    def user_profiles(self) -> Any:
        """Return loaded user profiles data, or None if not set."""
        return self._user_profiles

    def load_user_profiles(self, path: str) -> None:
        """Load user profiles from a JSON file and store data."""
        try:
            with open(path, encoding='utf-8') as profiles_file:
                self._user_profiles = json.load(profiles_file)
        except FileNotFoundError:
            logger.error("User profiles file not found at %s", path)
            self._user_profiles = None
        except json.JSONDecodeError:
            logger.error("Failed to parse user profiles JSON at %s", path)
            self._user_profiles = None

    def set_user_profiles(self, profiles: Any) -> None:
        """Set user profiles programmatically."""
        self._user_profiles = profiles

    @property
    def agent_configurations(self) -> dict[str, Any]:
        """Return loaded agent configurations mapped by profile/user key."""
        return self._agent_configurations

    def load_agent_configurations(self, path: str) -> None:
        """Load agent configurations from a JSON file.

        Expected format: a mapping where keys represent profile/user identifiers
        and values are the corresponding agent configuration objects.
        """
        try:
            with open(path, encoding='utf-8') as config_file:
                data = json.load(config_file)

            if isinstance(data, dict):
                self._agent_configurations = data
            else:
                logger.error("Agent configurations JSON at %s must be an object mapping keys to configurations", path)
                self._agent_configurations = {}
        except FileNotFoundError:
            logger.error("Agent configurations file not found at %s", path)
            self._agent_configurations = {}
        except json.JSONDecodeError:
            logger.error("Failed to parse agent configurations JSON at %s", path)
            self._agent_configurations = {}

    def set_agent_configurations(self, configurations: dict[str, Any] | None) -> None:
        """Set agent configurations programmatically.

        Args:
            configurations (dict[str, Any] | None): mapping of profile/user keys to config objects.
        """
        if configurations is None:
            self._agent_configurations = {}
            return

        if not isinstance(configurations, dict):
            raise TypeError("Agent configurations must be a dictionary mapping keys to configuration objects")
        self._agent_configurations = configurations

    def set_default_ic_config(self, ic_config: IntentClassifierConfiguration):
        """Set the default intent classifier configuration.

        Args:
            ic_config (IntentClassifierConfiguration): the intent classifier configuration
        """
        self._default_ic_config = ic_config

    def new_state(self,
                  name: str,
                  initial: bool = False,
                  ic_config: IntentClassifierConfiguration or None = None
                  ) -> State:
        """Create a new state in the agent.

        Args:
            name (str): the state name. It must be unique in the agent.
            initial (bool): whether the state is initial or not. An agent must have 1 initial state.
            ic_config (IntentClassifierConfiguration or None): the intent classifier configuration for the state.
                If None is provided, the agent's default one will be assigned to the state.

        Returns:
            State: the state
        """
        if not ic_config:
            ic_config = self._default_ic_config
        new_state = State(self, name, initial, ic_config)
        if new_state in self.states:
            raise DuplicatedStateError(self, new_state)
        if initial and self.initial_state():
            raise DuplicatedInitialStateError(self, self.initial_state(), new_state)
        self.states.append(new_state)
        return new_state

    # --- Reasoning extension ----------------------------------------------- #

    def add_tool(self, tool: Tool) -> Tool:
        """Add an already-constructed :class:`~baf.reasoning.tool.Tool` to the agent.

        Mirrors :meth:`add_intent`: the caller builds the wrapper, this method
        registers it. Use :meth:`new_tool` when you want to skip the explicit
        ``Tool(...)`` construction.

        Args:
            tool (Tool): the tool wrapper to register.

        Returns:
            Tool: the registered tool wrapper.
        """
        if tool.name in self._tools:
            logger.warning(f"[Agent] Replacing existing tool '{tool.name}'")
        self._tools[tool.name] = tool
        logger.info(f"[Agent] Registered tool: {tool.name}")
        return tool

    def new_tool(self, fn: Callable, name: str = None, description: str = None) -> Tool:
        """Build a :class:`~baf.reasoning.tool.Tool` from a callable and register it.

        See :class:`baf.reasoning.tool.Tool` for the auto-introspection rules.

        Args:
            fn (Callable): the function to expose. May be a bound method.
            name (str): override the tool's public name. Defaults to ``fn.__name__``.
            description (str): override the description shown to the LLM.
                Defaults to the first line of ``fn.__doc__``.

        Returns:
            Tool: the registered tool wrapper.
        """
        return self.add_tool(Tool(fn, name=name, description=description))

    def load_tools(self, path: str) -> list[Tool]:
        """Load every public top-level callable from a Python module or folder of modules.

        ``path`` may be a single ``.py`` file or a folder (non-recursive). For
        each module, every callable whose name does not start with ``_`` is
        registered as a tool. Callables imported from other modules are skipped
        — only those *defined* in the loaded module are considered, so importing
        helpers in ``tools.py`` does not pollute the tool registry.

        Args:
            path (str): path to a ``.py`` file or to a folder containing them.

        Returns:
            list[Tool]: the tools that were registered (may be empty).
        """
        target = Path(path)
        if not target.exists():
            raise FileNotFoundError(f"load_tools: path does not exist: {path}")

        if target.is_file():
            files = [target]
        else:
            files = sorted(p for p in target.iterdir() if p.is_file() and p.suffix == ".py")

        registered: list = []
        for file in files:
            module_name = f"baf_loaded_tools_{file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec is None or spec.loader is None:
                logger.warning(f"[Agent] Could not load tools from {file}: no spec")
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                logger.warning(f"[Agent] Failed to import tools from {file}: {e}")
                continue
            for member_name, member in inspect.getmembers(module):
                if member_name.startswith("_"):
                    continue
                if not callable(member):
                    continue
                # Skip classes and members imported from other modules.
                if inspect.isclass(member):
                    continue
                if getattr(member, "__module__", None) != module.__name__:
                    continue
                registered.append(self.new_tool(member))
        return registered

    def tool(self, fn: Callable = None, *, name: str = None, description: str = None):
        """Decorator form of :meth:`new_tool`.

        Usable bare (``@agent.tool``) or with arguments (``@agent.tool(name='x')``).
        """
        def _wrap(f: Callable) -> Callable:
            self.new_tool(f, name=name, description=description)
            return f
        if fn is None:
            return _wrap
        return _wrap(fn)

    def add_skill(self, skill: Skill) -> Skill:
        """Add an already-constructed :class:`~baf.reasoning.skill.Skill` to the agent.

        Mirrors :meth:`add_intent`. Use :meth:`new_skill` to skip the explicit
        ``Skill(...)`` construction (especially convenient for loading from a
        ``.md`` file path).

        Args:
            skill (Skill): the skill to register.

        Returns:
            Skill: the registered skill.
        """
        if skill.name in self._skills:
            logger.warning(f"[Agent] Replacing existing skill '{skill.name}'")
        self._skills[skill.name] = skill
        logger.info(f"[Agent] Registered skill: {skill.name}")
        return skill

    def new_skill(self, source: str, name: str = None, description: str = None) -> Skill:
        """Build a :class:`~baf.reasoning.skill.Skill` and register it.

        ``source`` is either a path to an existing ``.md`` file (loaded via
        :meth:`Skill.from_file`) or a literal markdown string. The path
        detection is automatic.

        Args:
            source (str): path to a ``.md`` file or the markdown content as a string.
            name (str): override the skill name (otherwise taken from frontmatter,
                a leading H1, or the filename stem).
            description (str): override the description (otherwise taken from
                frontmatter).

        Returns:
            Skill: the registered skill.
        """
        candidate = Path(source) if isinstance(source, str) else None
        if candidate is not None and candidate.is_file() and candidate.suffix.lower() == ".md":
            skill = Skill.from_file(str(candidate))
            if name:
                skill.name = name
            if description:
                skill.description = description
        else:
            skill = Skill(source, name=name, description=description)
        return self.add_skill(skill)

    def load_skills(self, folder: str) -> list[Skill]:
        """Register every ``*.md`` file in ``folder`` (non-recursive) as a skill.

        Args:
            folder (str): path to a folder containing markdown files.

        Returns:
            list[Skill]: the skills that were registered.
        """
        return [self.add_skill(s) for s in Skill.from_folder(folder)]

    def add_workspace(self, workspace: Workspace) -> Workspace:
        """Add an already-constructed :class:`~baf.reasoning.workspace.Workspace` to the agent.

        The first call also registers the universal ``list_directory`` /
        ``read_file`` tools, and — if at least one registered workspace has
        ``writable=True`` — the ``write_file`` / ``create_file`` /
        ``delete_file`` tools.

        Mirrors :meth:`add_intent`. Use :meth:`new_workspace` to skip the
        explicit ``Workspace(...)`` construction.

        Args:
            workspace (Workspace): the workspace to register.

        Returns:
            Workspace: the registered workspace.

        Raises:
            ValueError: if a workspace with the same name is already registered.
        """
        if workspace.name in self._workspaces:
            raise ValueError(f"Workspace '{workspace.name}' is already registered")
        self._workspaces[workspace.name] = workspace
        self._ensure_workspace_tools_registered()
        logger.info(f"[Agent] Registered workspace: {workspace.name} "
                    f"(root={workspace.root}, writable={workspace.writable})")
        return workspace

    def new_workspace(self, path: str, name: str = "workspace",
                      description: str = None,
                      writable: bool = True,
                      max_read_bytes: int = 200_000) -> Workspace:
        """Build a :class:`~baf.reasoning.workspace.Workspace` and register it.

        Args:
            path (str): the workspace root path.
            name (str): the workspace identifier the LLM passes as the
                ``workspace`` tool argument. Must be unique within the agent.
            description (str): a short human-readable explanation of *what* the
                workspace contains. Strongly recommended — without it the LLM
                only sees the name and root path and may not realise it should
                browse the workspace.
            writable (bool): whether mutating operations are allowed on this
                workspace (``write_file`` / ``create_file`` / ``delete_file``).
                Defaults to True.
            max_read_bytes (int): cap on ``read_file`` output, in bytes.

        Returns:
            Workspace: the registered workspace.
        """
        return self.add_workspace(Workspace(
            path, name=name, description=description,
            writable=writable, max_read_bytes=max_read_bytes,
        ))

    def _resolve_workspace(self, name: str = None) -> 'Workspace':
        """Look up a workspace by name, or pick the only one when ``name`` is None.

        Raises a ``ValueError`` (which the Tool wrapper turns into an LLM-readable
        ERROR string) on missing or ambiguous lookups.
        """
        if name is None:
            if len(self._workspaces) == 1:
                return next(iter(self._workspaces.values()))
            if not self._workspaces:
                raise ValueError("No workspaces are registered")
            raise ValueError(
                f"Multiple workspaces are registered, please specify one of: "
                f"{list(self._workspaces.keys())}"
            )
        if name not in self._workspaces:
            raise ValueError(
                f"Workspace '{name}' not found. Available: {list(self._workspaces.keys())}"
            )
        return self._workspaces[name]

    def _ensure_workspace_tools_registered(self) -> None:
        """Register the universal workspace tools.

        Read tools (``list_directory``, ``read_file``) are registered as soon
        as any workspace exists. Write tools (``write_file``, ``create_file``,
        ``delete_file``) are registered only once at least one workspace has
        ``writable=True`` — read-only-only setups never expose them to the LLM.

        The tool callables themselves live in
        :mod:`baf.library.tool.workspace_tools`. This method only owns the
        gating policy (which family to expose, when) plus the dedup check.
        Idempotent — already-registered tools are skipped.
        """
        # Imported lazily to avoid pulling baf.library.tool at module load time.
        from baf.library.tool.workspace_tools import (
            build_workspace_read_tools,
            build_workspace_write_tools,
        )

        for fn in build_workspace_read_tools(self):
            if fn.__name__ not in self._tools:
                self.new_tool(fn)

        if any(ws.writable for ws in self._workspaces.values()):
            for fn in build_workspace_write_tools(self):
                if fn.__name__ not in self._tools:
                    self.new_tool(fn)

    def add_intent(self, intent: Intent) -> Intent:
        """Add an intent to the agent.

        Args:
            intent (Intent): the intent to add

        Returns:
            Intent: the added intent
        """
        if intent in self.intents:
            raise DuplicatedIntentError(self, intent)
        self.intents.append(intent)
        return intent

    def new_intent(self,
                   name: str,
                   training_sentences: list[str] or None = None,
                   parameters: list[IntentParameter] or None = None,
                   description: str or None = None,
                   ) -> Intent:
        """Create a new intent in the agent.

        Args:
            name (str): the intent name. It must be unique in the agent
            training_sentences (list[str] or None): the intent's training sentences
            parameters (list[IntentParameter] or None): the intent parameters, optional
            description (str or None): a description of the intent, optional

        Returns:
            Intent: the intent
        """
        new_intent = Intent(name, training_sentences, parameters, description)
        if new_intent in self.intents:
            raise DuplicatedIntentError(self, new_intent)
        self.intents.append(new_intent)
        return new_intent

    def add_entity(self, entity: Entity) -> Entity:
        """Add an entity to the agent.

        Args:
            entity (Entity): the entity to add

        Returns:
            Entity: the added entity
        """
        if entity in self.entities:
            raise DuplicatedEntityError(self, entity)
        self.entities.append(entity)
        return entity

    def new_entity(self,
                   name: str,
                   base_entity: bool = False,
                   entries: dict[str, list[str]] or None = None,
                   description: str or None = None
                   ) -> Entity:
        """Create a new entity in the agent.

        Args:
            name (str): the entity name. It must be unique in the agent
            base_entity (bool): whether the entity is a base entity or not (i.e. a custom entity)
            entries (dict[str, list[str]] or None): the entity entries
            description (str or None): a description of the entity, optional

        Returns:
            Entity: the entity
        """
        new_entity = Entity(name, base_entity, entries, description)
        if new_entity in self.entities:
            raise DuplicatedEntityError(self, new_entity)
        self.entities.append(new_entity)
        return new_entity

    def initial_state(self) -> State or None:
        """Get the agent's initial state. It can be None if it has not been set.

        Returns:
            State or None: the initial state of the agent, if exists
        """
        for state in self.states:
            if state.initial:
                return state
        return None

    def _init_global_states(self) -> None:
        """Initialise the global states and add the necessary transitions.

        Go through all the global states and add transitions to every state to jump to the global states.
        Also add the transition to jump back to the previous state once the global state component
        has been completed. 
        """
        if self.global_initial_states:
            global_state_follow_up = []
            for global_state_tuple in self.global_initial_states:
                global_state = global_state_tuple[0]
                for state in self.global_state_component[global_state]:
                    global_state_follow_up.append(state)
            for global_state_tuple in self.global_initial_states:
                global_state = global_state_tuple[0]
                for state in self.states:
                    if (not any(
                            state.name is global_init_state[0].name for global_init_state in self.global_initial_states)
                            and state not in global_state_follow_up):
                        if state.transitions and not state.transitions[0].is_auto():
                            state.when_intent_matched(global_state_tuple[1]).go_to(global_state)
                            self.global_state_component[global_state][-1].when_variable_matches_operation(
                                var_name="prev_state", operation=operator.eq, target=state).go_to(state)
            self.global_initial_states.clear()

    def _run_platforms(self) -> None:
        """Start the execution of the agent platforms"""
        for platform in self._platforms:
            thread = threading.Thread(target=platform.run)
            self._platforms_threads.append(thread)
            thread.start()

    def _stop_platforms(self) -> None:
        """Stop the execution of the agent platforms"""
        for platform, thread in zip(self._platforms, self._platforms_threads):
            try:
                platform.stop()
            except KeyboardInterrupt:
                logger.warning('Keyboard interrupt while stopping %s; forcing shutdown.', platform.__class__.__name__)
            except Exception as exc:
                logger.error('Error while stopping %s: %s', platform.__class__.__name__, exc)
            finally:
                if thread.is_alive():
                    thread.join(timeout=5)
        self._platforms_threads = []

    def run(self, train: bool = True, sleep: bool = True) -> None:
        """Start the execution of the agent.

        Args:
            train (bool): whether to train the agent or not
            sleep (bool): whether to sleep after running the agent or not, which means that this function will not return
        """
        if train:
            self.train()
        if not self._trained:
            raise AgentNotTrainedError(self)
        if self.get_property(DB_MONITORING):
            if not self._monitoring_db:
                self._monitoring_db = MonitoringDB()
            self._monitoring_db.connect_to_db(self)
            if self._monitoring_db.connected:
                self._monitoring_db.initialize_db()
            if not self._monitoring_db.connected and self._persist_sessions:
                logger.warning(f'Agent {self._name} persistence of sessions is enabled, but the monitoring database is not connected. Sessions will not be persisted.')
                self._persist_sessions = False
        self._run_platforms()
        # self._run_event_thread()
        if sleep:
            idle = threading.Event()
            while True:
                try:
                    idle.wait(1)
                except BaseException as e:
                    self.stop()
                    logger.info(f'{self._name} execution finished due to {e.__class__.__name__}')
                    break

    def stop(self) -> None:
        """Stop the agent execution."""
        logger.info(f'Stopping agent {self._name}')
        self._stop_platforms()
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.close_connection()
        if self._db_handler is not None:
            self._db_handler.close_all()

        for session_id in list(self._sessions.keys()):
            self.close_session(session_id)

    def reset(self, session_id: str) -> Session or None:
        """Reset the agent current state and memory for the specified session. Then, restart the agent again for this session.

        Args:
            session_id (str): the session to reset

        Returns:
            Session or None: the reset session, or None if the provided session_id does not exist
        """
        if session_id not in self._sessions:
            return None
        else:
            session = self._sessions[session_id]
            self.delete_session(session_id)
        self.get_or_create_session(session_id, session.platform)
        logger.info(f'{self._name} restarted by user {session_id}')

        return self._sessions[session_id]

    def receive_event(self, event: Event) -> None:
        """Receive an external event from a platform.

        Receiving an event and send it to all the applicable sessions of the agent

        Args:
            event (Event): the received event
        """
        session: Session = None
        if event.is_broadcasted():
            for session in self._sessions.values():
                session.events.appendleft(event)
                session._event_loop.call_soon_threadsafe(session.manage_transition)
        else:
            session = self._sessions[event.session_id]
            session.events.appendleft(event)
            session.call_manage_transition()
        self._monitoring_db_insert_event(event)
        if isinstance(event, ReceiveMessageEvent):
            if isinstance(event, ReceiveJSONEvent):
                t = MessageType.JSON
            else:
                t = MessageType.STR
            session.save_message(Message(t=t, content=event.message, is_user=True, timestamp=datetime.now()))
        if isinstance(event, ReceiveFileEvent):
            session.save_message(Message(t=MessageType.FILE, content=event.file.get_json_string(), is_user=True, timestamp=datetime.now()))

        logger.info(f'Received event: {event.log()}')

    def process(self, session: Session, message: Any, is_user_message: bool) -> Any:
        """Runs the agent processors in a message.

        Only processors that process messages of the same type as the given message will be run.
        If the message to process is a user message, only processors that process user messages will be run.
        If the message to process is an agent message, only processors that process agent messages will be run.

        Args:
            session (Session): the current session
            message (Any): the message to be processed
            is_user_message (bool): indicates whether the message is a user message (True) or an agent message (False)

        Returns:
            Any: the processed message
        """
        for processor in self.processors:
            method_return_type = get_type_hints(processor.process).get('return')
            if method_return_type is not None and isinstance(message, method_return_type):
                if (processor.agent_messages and not is_user_message) or (processor.user_messages and is_user_message):
                    message = processor.process(session=session, message=message)
        return message

    def set_global_fallback_body(self, body: Callable[[Session], None]) -> None:
        """Set the fallback body for all agent states.

        The fallback body is a state's callable function that will be run whenever necessary to handle unexpected
        scenarios (e.g. when no intent is matched, the current state's fallback is run). This method simply sets the
        same fallback body to all agent states.

        See also:
            :func:`~baf.core.state.State.set_fallback_body`

        Args:
            body (Callable[[Session], None]): the fallback body
        """
        for state in self.states:
            state.set_fallback_body(body)

    def train(self) -> None:
        """Train the agent.

        The agent training is done before its execution.
        """
        if not self.initial_state():
            raise InitialStateNotFound(self)
        self._init_global_states()
        self._nlp_engine.initialize()
        logger.info(f'{self._name} training started')
        self._nlp_engine.train()
        logger.info(f'{self._name} training finished')
        self._trained = True

    def _get_session(self, session_id: str) -> Session or None:
        """Get an agent session.

        Args:
            session_id (str): the session id

        Returns:
            Session or None: the session, if exists, or None
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        else:
            return None

    def _new_session(self, session_id: str, platform: Platform, username: str or None = None, session_name: str or None = None) -> Session:
        """Create a new session for the agent.

        Args:
            session_id (str): the session id
            platform (Platform): the platform where the session is to be created and used
            username (str): the name of the session user (optional)
            session_name (str): the name of the session (optional)

        Returns:
            Session: the session
        """
        if session_id in self._sessions:
            raise ValueError(f'Trying to create a new session with an existing id" {session_id}')
        if platform not in self._platforms:
            raise ValueError(f"Platform {platform.__class__.__name__} not found in agent '{self.name}'")
        session = Session(session_id, self, platform, username, session_name)
        self._sessions[session_id] = session
        if self._persist_sessions and self._monitoring_db_session_exists(session_id, platform):
            dest_state = self._monitoring_db_get_last_state_of_session(session_id, platform)
            if dest_state:
                for state in self.states:
                    if state.name == dest_state:
                        session._current_state = state
                        self._monitoring_db_load_session_variables(session)
                        break

        else:
            self._monitoring_db_insert_session(session)
            session.current_state.run(session)

        # ADD LOOP TO CHECK TRANSITIONS HERE
        session._run_event_thread()
        return session

    def get_or_create_session(self, session_id: str, platform: Platform, username: str or None = None, session_name: str or None = None) -> Session:
        session = self._get_session(session_id)
        if session is None:
            session = self._new_session(session_id, platform, username, session_name)
        return session

    def close_session(self, session_id: str) -> None:
        """Delete an existing agent session.

        Args:
            session_id (str): the session id
        """
        while self._sessions[session_id]._agent_connections:
            agent_connection = next(iter(self._sessions[session_id]._agent_connections.values()))
            agent_connection.close()
        self._sessions[session_id]._stop_event_thread()
        del self._sessions[session_id]

    def delete_session(self, session_id: str) -> None:
        """Delete an existing agent session.

        Args:
            session_id (str): the session id
        """
        while self._sessions[session_id]._agent_connections:
            agent_connection = next(iter(self._sessions[session_id]._agent_connections.values()))
            agent_connection.close()
        self._sessions[session_id]._stop_event_thread()
        self._monitoring_db_delete_session(self._sessions[session_id])
        del self._sessions[session_id]

    def use_websocket_platform(
            self,
            use_ui: bool = True,
            authenticate_users: bool = False,
    ) -> WebSocketPlatform:
        """Use the :class:`~baf.platforms.websocket.websocket_platform.WebSocketPlatform` on this agent.

        Args:
            use_ui (bool): if true, the default UI will be run to use this platform
            authenticate_users (bool): whether to enable user persistence and authentication. 
                         Requires streamlit database configuration. Default is False
        Returns:
            WebSocketPlatform: the websocket platform
        """
        websocket_platform = WebSocketPlatform(
            self,
            use_ui,
            authenticate_users,
        )
        self._platforms.append(websocket_platform)
        return websocket_platform

    def use_telegram_platform(self) -> TelegramPlatform:
        """Use the :class:`~baf.platforms.telegram.telegram_platform.TelegramPlatform` on this agent.

        Returns:
            TelegramPlatform: the telegram platform
        """
        telegram_platform = TelegramPlatform(self)
        self._platforms.append(telegram_platform)
        return telegram_platform

    def use_github_platform(self) -> GitHubPlatform:
        """Use the :class:`~baf.platforms.github.github_platform.GitHubPlatform` on this agent.

        Returns:
            GitHubPlatform: the GitHub platform
        """
        github_platform = GitHubPlatform(self)
        self._platforms.append(github_platform)
        return github_platform

    def use_gitlab_platform(self) -> GitLabPlatform:
        """Use the :class:`~baf.platforms.gitlab.gitlab_platform.GitLabPlatform` on this agent.

        Returns:
            GitLabPlatform: the GitLab platform
        """
        gitlab_platform = GitLabPlatform(self)
        self._platforms.append(gitlab_platform)
        return gitlab_platform
    
    def use_a2a_platform(self) -> A2APlatform:
        """Use the :class: `~baf.platforms.a2a.a2a_platform.A2APlatform` on this agent.

        Returns:
            A2APlatform: the A2A platform
        """
        a2a_platform = A2APlatform(self)
        self._platforms.append(a2a_platform)
        return a2a_platform

    def use_db_handler(self) -> DBHandler:
        """Use the :class:`~baf.db.db_handler.DBHandler` on this agent.

        DB connections are established lazily, when the first query is executed.

        Returns:
            DBHandler: the database handler
        """
        if self._db_handler is None:
            self._db_handler = DBHandler(self)
        return self._db_handler

    def _monitoring_db_insert_session(self, session: Session) -> None:
        """Insert a session record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            # Not in thread since we must ensure it is added before running a state (the chat table needs the session)
            self._monitoring_db.insert_session(session)

    def _monitoring_db_session_exists(self, session_id: str, platform: Platform) -> bool:
        """
        Check if a session with the given session_id exists in the monitoring database.

        Args:
            session_id (str): The session ID to check.
            platform (Platform): The platform to check.

        Returns:
            bool: True if the session exists in the database, False otherwise
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db and self._monitoring_db.connected:
            result = self._monitoring_db.session_exists(self.name, platform.__class__.__name__, session_id)
            return result
        return False

    def _monitoring_db_get_last_state_of_session(
            self,
            session_id: str,
            platform: Platform
    ) -> str | None:
        """Get the last state of a session from the monitoring database.

        Args:
            session_id (str): The session ID to check.
            platform (Platform): The platform to check.

        Returns:
            str | None: The last state of the session if it exists, None otherwise.
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db and self._monitoring_db.connected:
            return self._monitoring_db.get_last_state_of_session(self.name, platform.__class__.__name__, session_id)
        return None

    def _monitoring_db_store_session_variables(
            self,
            session: Session
    ) -> None:
        """Store the session variables (private data dictionary) in the monitoring database.

        Args:
            session (Session): The session to store the variables for.
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.store_session_variables(session)

    def _monitoring_db_load_session_variables(
            self,
            session: Session
    ) -> None:
        """Load the session variables (private data dictionary) from the monitoring database.

        Args:
            session (Session): The session to load the variables for.
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.load_session_variables(session)

    def _monitoring_db_delete_session(self, session: Session) -> None:
        """Delete a session record from the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            # Not in thread since we must ensure it is deleted before removing the session
            self._monitoring_db.delete_session(session)

    def _monitoring_db_insert_intent_prediction(
            self,
            session: Session,
            predicted_intent: IntentClassifierPrediction
    ) -> None:
        """Insert an intent prediction record into the monitoring database.

        Args:
            session (Session): the session of the current user
            predicted_intent (IntentClassifierPrediction): the intent prediction
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_intent_prediction,
                                      args=(session, session.current_state, predicted_intent))
            thread.start()

    def _monitoring_db_insert_transition(self, session: Session, transition: Transition) -> None:
        """Insert a transition record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_transition, args=(session, transition))
            thread.start()

    def _monitoring_db_insert_chat(self, session: Session, message: Message) -> None:
        """Insert a message record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_chat, args=(session, message))
            thread.start()

    def _monitoring_db_insert_reasoning_event(
        self,
        session: Session,
        kind: str,
        payload: Any,
    ) -> None:
        """Insert a reasoning-state event (step or task-list snapshot) into the
        dedicated ``reasoning_step`` table. Synchronous on purpose so a
        subsequent ``link_pending_reasoning_events`` call sees the row.
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.insert_reasoning_event(session, kind, payload)

    def _monitoring_db_select_reasoning_events(
        self,
        session: Session,
        until_timestamp=None,
    ):
        """Fetch all reasoning events for a session, in chronological order."""
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            return self._monitoring_db.select_reasoning_events(
                session, until_timestamp=until_timestamp,
            )
        return None

    def _monitoring_db_link_pending_reasoning_events(self, session: Session) -> None:
        """Attach reasoning events with chat_id IS NULL to the most recent
        chat row for ``session``. Best-effort, called at the end of every
        reasoning loop."""
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.link_pending_reasoning_events(session)

    def _monitoring_db_insert_event(self, event: Event) -> None:
        """Insert an event record into the monitoring database.

        Args:
            event (Event): the event to insert into the database
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            if event.is_broadcasted():
                session = None
            else:
                session = self._sessions[event.session_id]
            thread = threading.Thread(target=self._monitoring_db.insert_event, args=(session, event))
            thread.start()
