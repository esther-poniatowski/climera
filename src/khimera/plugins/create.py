#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
khimera.plugins.create
======================

Standardized interface for creating plugins, on the plugin provider side.

Classes
-------
Plugin
    Represents the components of a plugin.
Components
    Type for a list of components of a plugin.

See Also
--------
khimera.plugins.core
khimera.plugins.declare
"""
from typing import Optional, Type, Dict, Self
import copy

from khimera.utils.factories import TypeConstrainedDict, TypeConstrainedList
from khimera.components.core import Component, ComponentSet
from khimera.plugins.declare import PluginModel


class Plugin:
    """
    Represents the components of a plugin.

    Attributes
    ----------
    model : PluginModel
        Plugin model specifying the expected structure and components of the plugin.
    name : str
        Name of the plugin.
    components : Dict[str, ComponentSet]
        Components of the plugin for each specification field in the plugin model.
        Keys: Names of the specification fields declared in the plugin model.
        Values: Contribution(s) for each field. If the specification sets expects one unique
        component, the list should contain only one element.

    Examples
    --------
    Import a plugin model from the host application:

    >>> from host_app.plugins.models import example_model

    Create a plugin with a name and version metadata for this model:

    >>> plugin = Plugin(model=example_model, name='my_plugin', version='1.0.0')

    Provide a command within a predefined sub-command group of the host application ('commands' field
    key in the model):

    >>> def my_command():
    ...     print("Plugin command executed")
    >>> plugin.add('commands', Command(name='my_cmd', callable=my_command, group='sub-command'))

    Provide a function to extend the host application's API ('api-functions' field key in the model):

    >>> def my_function():
    ...     print("Plugin function executed")
    >>> plugin.add('api-functions', APIExtension(name='my_func', callable=my_function))

    Provide a specific static resource processed by the host application ('input_file' field key in
    the model):

    >>> plugin.add('input_file', Asset(name='my_input', package="my_package", file_path="assets/logo.png"))

    Notes
    -----
    No validation of the components is performed when adding components to the plugin. The
    components are validated against the plugin model by the `PluginValidator` class in the
    module `khimera.plugins.validate`.

    Implications:

    - Any field (key) can be added to the plugin, regardless of the presence of the corresponding
      field in the model.
    - Multiple components can be added to the same field, regardless of the uniqueness
      constraints set by the corresponding field in the model.
    - Any type of component can be provided to the plugin, regardless of the expected category of
      the corresponding field in the model.
    """
    def __init__(self,
                model : PluginModel,
                name: str,
                version: Optional[str] = None,
                **kwargs
                ):
        self.model = model
        self.name = name
        self.version = version
        self.components = TypeConstrainedDict(str, ComponentSet) # automatic type checking
        for key, value in kwargs.items(): # add immediate contents of kwargs
            self.add(key=key, contrib=value)

    def __str__(self):
        """Print name and metadata of the plugin."""
        return f"Plugin(name={self.name}, version={self.version}, model={self.model})"

    def add(self, key: str, contrib: Component) -> Self:
        """
        Add a component to one of the specified fields in the plugin model.

        Arguments
        ---------
        key : str
            Key of the specification field in the plugin model.
        contrib : Component
            Contribution to add to the plugin.

        Returns
        -------
        Self
            Updated plugin instance, for method chaining.

        Raise
        -----
        TypeError
            If the `contrib` argument is not a subclass of `Component`. Automatically raised by the
            `TypeConstrainedList` class when adding the component to the list of components.
        """
        if key not in self.components: # initialize storage for the field
            self.components[key] = ComponentSet() # automatic type checking
        contrib.attach(self.name) # keep track of the plugin providing the component
        self.components[key].append(contrib)
        return self

    def remove(self, key: str, contrib_name: Optional[str] = None) -> Self:
        """
        Remove a component or all components for a specific key from the plugin.

        Arguments
        ---------
        key : str
            Key of the specification field in the plugin model.
        contrib_name : str, optional
            Name of the specific component to remove. If not provided, all components for the
            key are removed.

        Returns
        -------
        Self
            Updated plugin instance, for method chaining.

        Raises
        ------
        KeyError
            If the key is not found in the plugin's components.
        ValueError
            If the specified component is not found for the given key.
        """
        if key not in self.components:
            raise KeyError(f"No key '{key}' in the plugin's components")
        if contrib_name is None:
            del self.components[key]
        else:
            try:
                contrib = next(contrib for contrib in self.components[key] if contrib.name == contrib_name)
                self.components[key].remove(contrib)
            except ValueError:
                raise ValueError(f"No component '{contrib_name}' for key '{key}'")
        return self

    def get(self, key: str) -> ComponentSet:
        """
        Get the components of the plugin for a specific field.

        Arguments
        ---------
        key : str
            Key of the field in the plugin model.

        Returns
        -------
        ComponentSet
            Components of the plugin stored for the specified field.
        """
        return self.components.get(key, [])

    def filter(self, category: Optional[Type[Component]] = None) -> Dict[str, ComponentSet]:
        """
        Get the components of the plugin, optionally filtered by category.

        Arguments
        ---------
        category : Type[Component]
            Category of the components to filter. If not provided, all components are
            returned.

        Returns
        -------
        TypeConstrainedDict[str, ComponentSet]
            Components of the plugin, filtered by category if provided.
        """
        if category:
            return {key: contribs for key, contribs in self.components.items() if any(isinstance(item, category) for item in contribs)}
        return self.components

    def copy(self) -> Self:
        """
        Create a deep copy of the plugin, creating copies of all its nested components.

        Returns
        -------
        Plugin
            Copy of the plugin instance.

        See Also
        --------
        copy.deepcopy
        """
        return copy.deepcopy(self)
