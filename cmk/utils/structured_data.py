#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""
This module handles tree structures for HW/SW Inventory system and
structured monitoring data of Check_MK.
"""

from __future__ import annotations

import gzip
import io
import pprint
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal, NamedTuple, TypedDict

from cmk.utils import store
from cmk.utils.type_defs import HostName

# TODO Cleanup path in utils, base, gui, find ONE place (type defs or similar)
# TODO
# - is_equal -> __eq__/__ne__
# - merge_with -> __add__
# - count_entries -> __len__?
# TODO Improve/clarify adding Attributes/Table while deserialization/filtering/merging/...

# TODO improve this
SDRawTree = dict
SDRawDeltaTree = dict

SDNodeName = str
SDPath = tuple[SDNodeName, ...]

SDKey = str
# TODO be more specific (None, str, float, int, DeltaValue:Tuple of previous)
SDValue = Any  # needs only to support __eq__

SDPairs = dict[SDKey, SDValue]
# TODO merge with cmk.base.api.agent_based.inventory_classes.py::AttrDict
SDPairsFromPlugins = Mapping[SDKey, SDValue]
LegacyPairs = dict[SDKey, SDValue]

# TODO SDRows and LegacyRows are the same for now, but SDRows will change in the future
# adapt werk 12389 if inner table structure changes from list[SDRow] to dict[SDRowIdent, SDRow]
SDKeyColumns = list[SDKey]
SDRowIdent = tuple[SDValue, ...]
SDRow = dict[SDKey, SDValue]
SDRows = dict[SDRowIdent, SDRow]
LegacyRows = list[SDRow]

# Used for de/serialization and retentions
ATTRIBUTES_KEY = "Attributes"
TABLE_KEY = "Table"

_PAIRS_KEY = "Pairs"
_KEY_COLUMNS_KEY = "KeyColumns"
_ROWS_KEY = "Rows"
_NODES_KEY = "Nodes"
_RETENTIONS_KEY = "Retentions"


class _RawIntervalFromConfigMandatory(TypedDict):
    interval: int
    visible_raw_path: str


class _RawIntervalFromConfig(_RawIntervalFromConfigMandatory, total=False):
    attributes: Literal["all"] | tuple[str, list[str]]
    columns: Literal["all"] | tuple[str, list[str]]


RawIntervalsFromConfig = Sequence[_RawIntervalFromConfig]


class RetentionIntervals(NamedTuple):
    cached_at: int
    cache_interval: int
    retention_interval: int

    @property
    def valid_until(self) -> int:
        return self.cached_at + self.cache_interval

    @property
    def keep_until(self) -> int:
        return self.cached_at + self.cache_interval + self.retention_interval

    def serialize(self) -> tuple[int, int, int]:
        return self.cached_at, self.cache_interval, self.retention_interval

    @classmethod
    def deserialize(cls, raw_intervals: tuple[int, int, int]) -> RetentionIntervals:
        return cls(*raw_intervals)


RawRetentionIntervalsByKeys = dict[SDKey, tuple[int, int, int]]
RetentionIntervalsByKeys = dict[SDKey, RetentionIntervals]


@dataclass(frozen=True)
class UpdateResult:
    reasons_by_path: dict[SDPath, list[str]] = field(default_factory=dict)

    @property
    def save_tree(self) -> bool:
        return bool(self.reasons_by_path)

    @classmethod
    def from_results(cls, results: Iterable[UpdateResult]) -> UpdateResult:
        update_result = cls()
        for result in results:
            for path, reasons in result.reasons_by_path.items():
                update_result.reasons_by_path.setdefault(path, []).extend(reasons)
        return update_result

    def add_attr_reason(self, path: SDPath, name: str, iterable: Iterable[str]) -> None:
        self.reasons_by_path.setdefault(path, []).append(
            f"[Attributes] Added {name}: {', '.join(iterable)}"
        )

    def add_row_reason(
        self, path: SDPath, ident: SDRowIdent, name: str, iterable: Iterable[str]
    ) -> None:
        self.reasons_by_path.setdefault(path, []).append(
            f"[Table] '{', '.join(ident)}': Added {name}: {', '.join(iterable)}"
        )

    def __repr__(self) -> str:
        if not self.reasons_by_path:
            return "No tree update.\n"

        lines = ["Updated inventory tree:"]
        for path, reasons in self.reasons_by_path.items():
            lines.append(f"  Path '{' > '.join(path)}':")
            lines.extend(f"    {r}" for r in reasons)
        return "\n".join(lines) + "\n"


def parse_visible_raw_path(raw_path: str) -> SDPath:
    return tuple(part for part in raw_path.split(".") if part)


#   .--filters-------------------------------------------------------------.
#   |                       __ _ _ _                                       |
#   |                      / _(_) | |_ ___ _ __ ___                        |
#   |                     | |_| | | __/ _ \ '__/ __|                       |
#   |                     |  _| | | ||  __/ |  \__ \                       |
#   |                     |_| |_|_|\__\___|_|  |___/                       |
#   |                                                                      |
#   '----------------------------------------------------------------------'

# TODO filter table rows?


SDFilterFunc = Callable[[SDKey], bool]


class SDFilter(NamedTuple):
    path: SDPath
    filter_nodes: SDFilterFunc
    filter_attributes: SDFilterFunc
    filter_columns: SDFilterFunc


def make_filter_from_choice(
    choice: tuple[str, Sequence[str]] | Literal["nothing"] | Literal["all"] | None
) -> SDFilterFunc:
    def _make_choices_filter(choices: Sequence[str | int]) -> SDFilterFunc:
        return lambda key: key in choices

    # TODO Improve:
    # For contact groups (via make_filter)
    #   - ('choices', ['some', 'keys'])
    #   - 'nothing' -> _use_nothing
    #   - None -> _use_all
    # For retention intervals (directly)
    #   - ('choices', ['some', 'keys'])
    #   - MISSING (see mk/base/agent_based/inventory.py::_get_intervals_from_config) -> _use_nothing
    #   - 'all' -> _use_all
    if isinstance(choice, tuple):
        return _make_choices_filter(choice[-1])
    if choice == "nothing":
        return lambda k: False
    return lambda k: True


# .
#   .--mutable tree--------------------------------------------------------.
#   |                      _        _     _        _                       |
#   |      _ __ ___  _   _| |_ __ _| |__ | | ___  | |_ _ __ ___  ___       |
#   |     | '_ ` _ \| | | | __/ _` | '_ \| |/ _ \ | __| '__/ _ \/ _ \      |
#   |     | | | | | | |_| | || (_| | |_) | |  __/ | |_| | |  __/  __/      |
#   |     |_| |_| |_|\__,_|\__\__,_|_.__/|_|\___|  \__|_|  \___|\___|      |
#   |                                                                      |
#   '----------------------------------------------------------------------'


class MutableTree:
    def __init__(self, tree: StructuredDataNode | None = None) -> None:
        self.tree: Final = StructuredDataNode() if tree is None else tree

    def __bool__(self) -> bool:
        return bool(self.tree)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (MutableTree, ImmutableTree)):
            raise TypeError(type(other))
        return self.tree.is_equal(other.tree)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def add_pairs(
        self,
        *,
        path: list[str],
        pairs: Mapping[str, int | float | str | None],
    ) -> None:
        self.tree.setdefault_node(tuple(path)).attributes.add_pairs(pairs)

    def add_rows(
        self,
        *,
        path: list[str],
        key_columns: list[str],
        rows: Sequence[Mapping[str, int | float | str | None]],
    ) -> None:
        node = self.tree.setdefault_node(tuple(path))
        node.table.add_key_columns(sorted(key_columns))
        node.table.add_rows(rows)

    def count_entries(self) -> int:
        return self.tree.count_entries()

    def get_attribute(self, path: SDPath, key: str) -> int | float | str | None:
        return (
            None if (node := self.tree.get_node(path)) is None else node.attributes.pairs.get(key)
        )

    def get_tree(self, path: SDPath) -> MutableTree:
        return MutableTree(self.tree.get_node(path))

    def has_table(self, path: SDPath) -> bool:
        return bool(self.tree.get_table(path))


# .
#   .--immutable tree------------------------------------------------------.
#   |          _                           _        _     _                |
#   |         (_)_ __ ___  _ __ ___  _   _| |_ __ _| |__ | | ___           |
#   |         | | '_ ` _ \| '_ ` _ \| | | | __/ _` | '_ \| |/ _ \          |
#   |         | | | | | | | | | | | | |_| | || (_| | |_) | |  __/          |
#   |         |_|_| |_| |_|_| |_| |_|\__,_|\__\__,_|_.__/|_|\___|          |
#   |                                                                      |
#   |                          _                                           |
#   |                         | |_ _ __ ___  ___                           |
#   |                         | __| '__/ _ \/ _ \                          |
#   |                         | |_| | |  __/  __/                          |
#   |                          \__|_|  \___|\___|                          |
#   |                                                                      |
#   '----------------------------------------------------------------------'


def _filter_attributes(attributes: Attributes, filter_func: SDFilterFunc) -> Attributes:
    filtered = Attributes(retentions=attributes.retentions)
    filtered.add_pairs(_get_filtered_dict(attributes.pairs, filter_func))
    return filtered


def _filter_table(table: Table, filter_func: SDFilterFunc) -> Table:
    filtered = Table(key_columns=table.key_columns, retentions=table.retentions)
    for ident, row in table.rows_by_ident.items():
        filtered.add_row(ident, _get_filtered_dict(row, filter_func))
    return filtered


def _filter_node(node: StructuredDataNode, filters: Iterable[SDFilter]) -> StructuredDataNode:
    filtered = StructuredDataNode(path=node.path)

    for f in filters:
        # First check if node exists
        if (child := node.get_node(f.path)) is None:
            continue

        filtered_node = StructuredDataNode(
            path=f.path,
            attributes=_filter_attributes(child.attributes, f.filter_attributes),
            table=_filter_table(child.table, f.filter_columns),
        )
        for name, sub_node in child.nodes_by_name.items():
            # From GUI::permitted_paths: We always get a list of strs.
            if f.filter_nodes(str(name)):
                filtered_node.add_node((str(name),), sub_node)

        filtered.add_node(f.path, filtered_node)

    return filtered


def _merge_attributes(left: Attributes, right: Attributes) -> Attributes:
    attributes = Attributes(retentions={**left.retentions, **right.retentions})
    attributes.add_pairs(left.pairs)
    attributes.add_pairs(right.pairs)
    return attributes


def _merge_tables_by_same_or_empty_key_columns(
    key_columns: SDKeyColumns, left: Table, right: Table
) -> Table:
    table = Table(
        key_columns=key_columns,
        retentions={**left.retentions, **right.retentions},
    )

    compared_keys = _compare_dict_keys(old_dict=right.rows_by_ident, new_dict=left.rows_by_ident)

    for key in compared_keys.only_old:
        table.add_row(key, right.rows_by_ident[key])

    for key in compared_keys.both:
        table.add_row(key, {**left.rows_by_ident[key], **right.rows_by_ident[key]})

    for key in compared_keys.only_new:
        table.add_row(key, left.rows_by_ident[key])

    return table


def _merge_tables(left: Table, right: Table) -> Table:
    if left.key_columns and not right.key_columns:
        return _merge_tables_by_same_or_empty_key_columns(left.key_columns, left, right)

    if not left.key_columns and right.key_columns:
        return _merge_tables_by_same_or_empty_key_columns(right.key_columns, left, right)

    if left.key_columns == right.key_columns:
        return _merge_tables_by_same_or_empty_key_columns(left.key_columns, left, right)

    # Re-calculate row identifiers for legacy tables or inventory and status tables
    table = Table(
        key_columns=sorted(set(left.key_columns).intersection(right.key_columns)),
        retentions={**left.retentions, **right.retentions},
    )
    table.add_rows(list(left.rows_by_ident.values()))
    table.add_rows(list(right.rows_by_ident.values()))
    return table


def _merge_nodes(left: StructuredDataNode, right: StructuredDataNode) -> StructuredDataNode:
    node = StructuredDataNode(
        path=left.path,
        attributes=_merge_attributes(left.attributes, right.attributes),
        table=_merge_tables(left.table, right.table),
    )

    compared_keys = _compare_dict_keys(old_dict=right.nodes_by_name, new_dict=left.nodes_by_name)

    for key in compared_keys.only_old:
        node.add_node((key,), right.nodes_by_name[key])

    for key in compared_keys.both:
        node.add_node(
            (key,),
            _merge_nodes(left=left.nodes_by_name[key], right=right.nodes_by_name[key]),
        )

    for key in compared_keys.only_new:
        node.add_node((key,), left.nodes_by_name[key])

    return node


def _new_delta_tree_node(value: SDValue) -> tuple[None, SDValue]:
    return (None, value)


def _removed_delta_tree_node(value: SDValue) -> tuple[SDValue, None]:
    return (value, None)


def _changed_delta_tree_node(old_value: SDValue, new_value: SDValue) -> tuple[SDValue, SDValue]:
    return (old_value, new_value)


def _identical_delta_tree_node(value: SDValue) -> tuple[SDValue, SDValue]:
    return (value, value)


class ComparedDictResult(NamedTuple):
    result_dict: dict[SDKey, tuple[SDValue | None, SDValue | None]]
    has_changes: bool


def _compare_dicts(
    *, old_dict: Mapping, new_dict: Mapping, keep_identical: bool
) -> ComparedDictResult:
    """
    Format of compared entries:
      new:          {k: (None, new_value), ...}
      changed:      {k: (old_value, new_value), ...}
      removed:      {k: (old_value, None), ...}
      identical:    {k: (value, value), ...}
    """
    compared_keys = _compare_dict_keys(old_dict=old_dict, new_dict=new_dict)
    compared_dict: dict[SDKey, tuple[SDValue | None, SDValue | None]] = {}

    has_changes = False
    for k in compared_keys.both:
        if (new_value := new_dict[k]) != (old_value := old_dict[k]):
            compared_dict.setdefault(k, _changed_delta_tree_node(old_value, new_value))
            has_changes = True
        elif keep_identical:
            compared_dict.setdefault(k, _identical_delta_tree_node(old_value))

    compared_dict.update({k: _new_delta_tree_node(new_dict[k]) for k in compared_keys.only_new})
    compared_dict.update({k: _removed_delta_tree_node(old_dict[k]) for k in compared_keys.only_old})

    return ComparedDictResult(
        result_dict=compared_dict,
        has_changes=bool(has_changes or compared_keys.only_new or compared_keys.only_old),
    )


def _compare_attributes(left: Attributes, right: Attributes) -> DeltaAttributes:
    return DeltaAttributes(
        pairs=_compare_dicts(
            old_dict=right.pairs,
            new_dict=left.pairs,
            keep_identical=False,
        ).result_dict,
    )


def _compare_tables(left: Table, right: Table) -> DeltaTable:
    key_columns = sorted(set(left.key_columns).union(right.key_columns))
    compared_keys = _compare_dict_keys(old_dict=right._rows, new_dict=left._rows)

    delta_rows: list[dict[SDKey, tuple[SDValue | None, SDValue | None]]] = []

    for key in compared_keys.only_old:
        delta_rows.append({k: _removed_delta_tree_node(v) for k, v in right._rows[key].items()})

    for key in compared_keys.both:
        # Note: Rows which have at least one change also provide all table fields.
        # Example:
        # If the version of a package (below "Software > Packages") has changed from 1.0 to 2.0
        # then it would be very annoying if the rest of the row is not shown.
        if (
            compared_dict_result := _compare_dicts(
                old_dict=right._rows[key],
                new_dict=left._rows[key],
                keep_identical=True,
            )
        ).has_changes:
            delta_rows.append(compared_dict_result.result_dict)

    for key in compared_keys.only_new:
        delta_rows.append({k: _new_delta_tree_node(v) for k, v in left._rows[key].items()})

    return DeltaTable(
        key_columns=key_columns,
        rows=delta_rows,
    )


def _compare_nodes(left: StructuredDataNode, right: StructuredDataNode) -> DeltaStructuredDataNode:
    delta_nodes: dict[SDNodeName, DeltaStructuredDataNode] = {}

    compared_keys = _compare_dict_keys(old_dict=right.nodes_by_name, new_dict=left.nodes_by_name)

    for key in compared_keys.only_new:
        child_left = left.nodes_by_name[key]
        if child_left.count_entries():
            delta_nodes[key] = DeltaStructuredDataNode.make_from_node(
                node=child_left,
                encode_as=_new_delta_tree_node,
            )

    for key in compared_keys.both:
        child_left = left.nodes_by_name[key]
        child_right = right.nodes_by_name[key]
        if child_left.is_equal(child_right):
            continue

        delta_node_result = _compare_nodes(child_left, child_right)
        if delta_node_result.count_entries():
            delta_nodes[key] = delta_node_result

    for key in compared_keys.only_old:
        child_right = right.nodes_by_name[key]
        if child_right.count_entries():
            delta_nodes[key] = DeltaStructuredDataNode.make_from_node(
                node=child_right,
                encode_as=_removed_delta_tree_node,
            )

    return DeltaStructuredDataNode(
        path=left.path,
        attributes=_compare_attributes(left.attributes, right.attributes),
        table=_compare_tables(left.table, right.table),
        _nodes=delta_nodes,
    )


class ImmutableTree:
    def __init__(self, tree: StructuredDataNode | None = None) -> None:
        self.tree: Final = StructuredDataNode() if tree is None else tree

    @classmethod
    def deserialize(cls, raw_tree: SDRawTree) -> ImmutableTree:
        return cls(StructuredDataNode.deserialize(raw_tree))

    def serialize(self) -> SDRawTree:
        return self.tree.serialize()

    def __bool__(self) -> bool:
        return bool(self.tree)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (MutableTree, ImmutableTree)):
            raise TypeError(type(other))
        return self.tree.is_equal(other.tree)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def filter(self, filters: Iterable[SDFilter]) -> ImmutableTree:
        return ImmutableTree(_filter_node(self.tree, filters))

    def merge(self, rhs: ImmutableTree) -> ImmutableTree:
        return ImmutableTree(_merge_nodes(self.tree, rhs.tree))

    def difference(self, rhs: ImmutableTree) -> ImmutableDeltaTree:
        return ImmutableDeltaTree(_compare_nodes(self.tree, rhs.tree))

    def get_attribute(self, path: SDPath, key: str) -> int | float | str | None:
        return (
            None if (node := self.tree.get_node(path)) is None else node.attributes.pairs.get(key)
        )

    def get_rows(self, path: SDPath) -> Sequence[SDRow]:
        return [] if (node := self.tree.get_node(path)) is None else node.table.rows

    def get_tree(self, path: SDPath) -> ImmutableTree:
        return ImmutableTree(self.tree.get_node(path))


# .
#   .--immutable delta tree------------------------------------------------.
#   |          _                           _        _     _                |
#   |         (_)_ __ ___  _ __ ___  _   _| |_ __ _| |__ | | ___           |
#   |         | | '_ ` _ \| '_ ` _ \| | | | __/ _` | '_ \| |/ _ \          |
#   |         | | | | | | | | | | | | |_| | || (_| | |_) | |  __/          |
#   |         |_|_| |_| |_|_| |_| |_|\__,_|\__\__,_|_.__/|_|\___|          |
#   |                                                                      |
#   |                  _      _ _          _                               |
#   |               __| | ___| | |_ __ _  | |_ _ __ ___  ___               |
#   |              / _` |/ _ \ | __/ _` | | __| '__/ _ \/ _ \              |
#   |             | (_| |  __/ | || (_| | | |_| | |  __/  __/              |
#   |              \__,_|\___|_|\__\__,_|  \__|_|  \___|\___|              |
#   |                                                                      |
#   '----------------------------------------------------------------------'


def _filter_delta_attributes(
    delta_attributes: DeltaAttributes, filter_func: SDFilterFunc
) -> DeltaAttributes:
    return DeltaAttributes(pairs=_get_filtered_dict(delta_attributes.pairs, filter_func))


def _filter_delta_table(delta_table: DeltaTable, filter_func: SDFilterFunc) -> DeltaTable:
    return DeltaTable(
        key_columns=delta_table.key_columns,
        rows=[
            filtered_row
            for row in delta_table.rows
            if (filtered_row := _get_filtered_dict(row, filter_func))
        ],
    )


def _filter_delta_node(
    delta_tree: DeltaStructuredDataNode, filters: Iterable[SDFilter]
) -> DeltaStructuredDataNode:
    filtered = DeltaStructuredDataNode(
        path=delta_tree.path,
        attributes=DeltaAttributes(pairs={}),
        table=DeltaTable(key_columns=[], rows=[]),
        _nodes={},
    )

    for f in filters:
        # First check if node exists
        node = delta_tree.get_node(f.path)
        if node is None:
            continue

        filtered.add_node(
            node.path,
            DeltaStructuredDataNode(
                path=node.path,
                attributes=_filter_delta_attributes(node.attributes, f.filter_attributes),
                table=_filter_delta_table(node.table, f.filter_columns),
                _nodes={
                    name: child
                    for name, child in node.nodes_by_name.items()
                    if f.filter_nodes(name)
                },
            ),
        )

    return filtered


class ImmutableDeltaTree:
    def __init__(self, tree: DeltaStructuredDataNode | None = None) -> None:
        self.tree: Final = tree or DeltaStructuredDataNode(
            path=tuple(),
            attributes=DeltaAttributes(pairs={}),
            table=DeltaTable(key_columns=[], rows=[]),
            _nodes={},
        )

    @classmethod
    def deserialize(cls, raw_tree: SDRawDeltaTree) -> ImmutableDeltaTree:
        return cls(DeltaStructuredDataNode.deserialize(raw_tree))

    def serialize(self) -> SDRawDeltaTree:
        return self.tree.serialize()

    def __bool__(self) -> bool:
        return bool(self.tree)

    def filter(self, filters: Iterable[SDFilter]) -> ImmutableDeltaTree:
        return ImmutableDeltaTree(_filter_delta_node(self.tree, filters))

    def get_stats(self) -> _SDDeltaCounter:
        return self.tree.count_entries()

    def get_tree(self, path: SDPath) -> ImmutableDeltaTree:
        return ImmutableDeltaTree(self.tree.get_node(path))


# .
#   .--IO------------------------------------------------------------------.
#   |                              ___ ___                                 |
#   |                             |_ _/ _ \                                |
#   |                              | | | | |                               |
#   |                              | | |_| |                               |
#   |                             |___\___/                                |
#   |                                                                      |
#   '----------------------------------------------------------------------'


# TODO Centralize different stores and loaders of tree files:
#   - inventory/HOSTNAME, inventory/HOSTNAME.gz, inventory/.last
#   - inventory_archive/HOSTNAME/TIMESTAMP,
#   - inventory_delta_cache/HOSTNAME/TIMESTAMP_{TIMESTAMP,None}
#   - status_data/HOSTNAME, status_data/HOSTNAME.gz


def load_tree(filepath: Path) -> ImmutableTree:
    if raw_tree := store.load_object_from_file(filepath, default=None):
        return ImmutableTree(StructuredDataNode.deserialize(raw_tree))
    return ImmutableTree()


class TreeStore:
    def __init__(self, tree_dir: Path | str) -> None:
        self._tree_dir = Path(tree_dir)
        self._last_filepath = Path(tree_dir) / ".last"

    def load(self, *, host_name: HostName) -> ImmutableTree:
        return load_tree(self._tree_file(host_name))

    def save(self, *, host_name: HostName, tree: StructuredDataNode, pretty: bool = False) -> None:
        self._tree_dir.mkdir(parents=True, exist_ok=True)

        tree_file = self._tree_file(host_name)

        output = tree.serialize()
        store.save_object_to_file(tree_file, output, pretty=pretty)

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write((repr(output) + "\n").encode("utf-8"))
        store.save_bytes_to_file(self._gz_file(host_name), buf.getvalue())

        # Inform Livestatus about the latest inventory update
        self._last_filepath.touch()

    def remove(self, *, host_name: HostName) -> None:
        self._tree_file(host_name).unlink(missing_ok=True)
        self._gz_file(host_name).unlink(missing_ok=True)

    def _tree_file(self, host_name: HostName) -> Path:
        return self._tree_dir / str(host_name)

    def _gz_file(self, host_name: HostName) -> Path:
        return self._tree_dir / f"{host_name}.gz"


class TreeOrArchiveStore(TreeStore):
    def __init__(self, tree_dir: Path | str, archive: Path | str) -> None:
        super().__init__(tree_dir)
        self._archive_dir = Path(archive)

    def load_previous(self, *, host_name: HostName) -> ImmutableTree:
        if (tree_file := self._tree_file(host_name=host_name)).exists():
            return load_tree(tree_file)

        try:
            latest_archive_tree_file = max(
                self._archive_host_dir(host_name).iterdir(), key=lambda tp: int(tp.name)
            )
        except (FileNotFoundError, ValueError):
            return ImmutableTree()

        return load_tree(latest_archive_tree_file)

    def _archive_host_dir(self, host_name: HostName) -> Path:
        return self._archive_dir / str(host_name)

    def archive(self, *, host_name: HostName) -> None:
        if not (tree_file := self._tree_file(host_name)).exists():
            return
        target_dir = self._archive_host_dir(host_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        tree_file.rename(target_dir / str(int(tree_file.stat().st_mtime)))
        self._gz_file(host_name).unlink(missing_ok=True)


# .
#   .--tree----------------------------------------------------------------.
#   |                          _                                           |
#   |                         | |_ _ __ ___  ___                           |
#   |                         | __| '__/ _ \/ _ \                          |
#   |                         | |_| | |  __/  __/                          |
#   |                          \__|_|  \___|\___|                          |
#   |                                                                      |
#   '----------------------------------------------------------------------'


class StructuredDataNode:
    def __init__(
        self,
        *,
        path: SDPath | None = None,
        attributes: Attributes | None = None,
        table: Table | None = None,
    ) -> None:
        self.path = path if path else tuple()
        self.attributes = attributes or Attributes()
        self.table = table or Table()
        self._nodes: dict[SDNodeName, StructuredDataNode] = {}

    @property
    def nodes(self) -> Iterator[StructuredDataNode]:
        yield from self._nodes.values()

    @property
    def nodes_by_name(self) -> Mapping[SDNodeName, StructuredDataNode]:
        return self._nodes

    #   ---common methods-------------------------------------------------------

    def __bool__(self) -> bool:
        if self.attributes or self.table:
            return True

        for node in self._nodes.values():
            if node:
                return True

        return False

    def is_equal(self, other: object) -> bool:
        if not isinstance(other, StructuredDataNode):
            raise TypeError(f"Cannot compare {type(self)} with {type(other)}")

        if not (self.attributes.is_equal(other.attributes) and self.table.is_equal(other.table)):
            return False

        compared_keys = _compare_dict_keys(old_dict=other._nodes, new_dict=self._nodes)
        if compared_keys.only_old or compared_keys.only_new:
            return False

        for key in compared_keys.both:
            if not self._nodes[key].is_equal(other._nodes[key]):
                return False
        return True

    def count_entries(self) -> int:
        return sum(
            [
                self.attributes.count_entries(),
                self.table.count_entries(),
            ]
            + [node.count_entries() for node in self._nodes.values()]
        )

    #   ---node methods---------------------------------------------------------

    def setdefault_node(self, path: SDPath) -> StructuredDataNode:
        if not path:
            return self

        name = path[0]
        node = self._nodes.setdefault(name, StructuredDataNode(path=self.path + (name,)))
        return node.setdefault_node(path[1:])

    def add_node(self, path: SDPath, node: StructuredDataNode) -> None:
        if not path:
            return

        node_name = path[0]
        node_path = self.path + (path[0],)
        if len(path) == 1:
            if node_name in self._nodes:
                merge_node = self._nodes[node_name]
            else:
                merge_node = StructuredDataNode(path=node_path)
            self._nodes[node_name] = _merge_nodes(merge_node, node)
            return

        self._nodes.setdefault(node_name, StructuredDataNode(path=node_path)).add_node(
            path[1:], node
        )

    def get_node(self, path: SDPath) -> StructuredDataNode | None:
        if not path:
            return self
        return None if (node := self._nodes.get(path[0])) is None else node.get_node(path[1:])

    def get_table(self, path: SDPath) -> Table | None:
        return None if (node := self.get_node(path)) is None else node.table

    def get_attributes(self, path: SDPath) -> Attributes | None:
        return None if (node := self.get_node(path)) is None else node.attributes

    #   ---representation-------------------------------------------------------

    def __repr__(self) -> str:
        # Only used for repr/debug purposes
        return f"{self.__class__.__name__}({pprint.pformat(self.serialize())})"

    #   ---de/serializing-------------------------------------------------------

    def serialize(self) -> SDRawTree:
        return {
            ATTRIBUTES_KEY: self.attributes.serialize(),
            TABLE_KEY: self.table.serialize(),
            _NODES_KEY: {name: node.serialize() for name, node in self._nodes.items()},
        }

    @classmethod
    def deserialize(cls, raw_tree: SDRawTree) -> StructuredDataNode:
        if all(key in raw_tree for key in (ATTRIBUTES_KEY, TABLE_KEY, _NODES_KEY)):
            return cls._deserialize(path=tuple(), raw_tree=raw_tree)
        return cls._deserialize_legacy(path=tuple(), raw_tree=raw_tree)

    @classmethod
    def _deserialize(
        cls,
        *,
        path: SDPath,
        raw_tree: SDRawTree,
    ) -> StructuredDataNode:
        node = cls(
            path=path,
            attributes=Attributes.deserialize(raw_pairs=raw_tree[ATTRIBUTES_KEY]),
            table=Table.deserialize(raw_rows=raw_tree[TABLE_KEY]),
        )

        for raw_name, raw_node in raw_tree[_NODES_KEY].items():
            node.add_node(
                (raw_name,),
                cls._deserialize(
                    path=path + (raw_name,),
                    raw_tree=raw_node,
                ),
            )

        return node

    @classmethod
    def _deserialize_legacy(
        cls,
        *,
        path: SDPath,
        raw_tree: SDRawTree,
    ) -> StructuredDataNode:
        raw_pairs: SDPairs = {}
        raw_tables: dict[tuple[str, ...], Any] = {}
        raw_nodes: SDRawTree = {}

        for key, value in raw_tree.items():
            if isinstance(value, dict):
                if not value:
                    continue
                raw_nodes.setdefault((str(key),), value)

            elif isinstance(value, list):
                if not value:
                    continue

                if all(not isinstance(v, (list, dict)) for row in value for v in row.values()):
                    # Either we get:
                    #   [
                    #       {"column1": "value 11", "column2": "value 12",...},
                    #       {"column1": "value 11", "column2": "value 12",...},
                    #       ...
                    #   ]
                    # Or:
                    #   [
                    #       {"attr": "attr1", "table": [...], "node": {...}, "idx-node": [...]},
                    #       ...
                    #   ]
                    raw_tables.setdefault((str(key),), value)
                    continue

                for idx, entry in enumerate(value):
                    raw_nodes.setdefault((str(key), str(idx)), entry)

            else:
                raw_pairs.setdefault(key, value)

        node = cls(
            path=path,
            attributes=Attributes._deserialize_legacy(legacy_pairs=raw_pairs),
        )

        for child_path, raw_table in raw_tables.items():
            node.add_node(
                child_path,
                cls(table=Table._deserialize_legacy(legacy_rows=raw_table)),
            )

        for child_path, raw_node in raw_nodes.items():
            node.add_node(
                child_path, cls._deserialize_legacy(path=path + child_path, raw_tree=raw_node)
            )

        return node


# TODO Table: {IDENT: Attributes}?

TableRetentions = dict[SDRowIdent, RetentionIntervalsByKeys]


class Table:
    def __init__(
        self,
        *,
        key_columns: SDKeyColumns | None = None,
        retentions: TableRetentions | None = None,
    ) -> None:
        self.key_columns = key_columns if key_columns else []
        self.retentions = retentions if retentions else {}
        self._rows: SDRows = {}

    def add_key_columns(self, key_columns: SDKeyColumns) -> None:
        for key in key_columns:
            if key not in self.key_columns:
                self.key_columns.append(key)

    @property
    def rows(self) -> list[SDRow]:
        return list(self._rows.values())

    @property
    def rows_by_ident(self) -> Mapping[SDRowIdent, SDRow]:
        return self._rows

    #   ---common methods-------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(self._rows)

    def is_equal(self, other: object) -> bool:
        if not isinstance(other, Table):
            raise TypeError(f"Cannot compare {type(self)} with {type(other)}")

        compared_keys = _compare_dict_keys(old_dict=other._rows, new_dict=self._rows)
        if compared_keys.only_old or compared_keys.only_new:
            return False

        for key in compared_keys.both:
            if self._rows[key] != other._rows[key]:
                return False
        return True

    def count_entries(self) -> int:
        return sum(map(len, self._rows.values()))

    #   ---table methods--------------------------------------------------------

    def add_rows(self, rows: Sequence[Mapping[str, int | float | str | None]]) -> None:
        for row in rows:
            self.add_row(self._make_row_ident(row), row)

    def _make_row_ident(self, row: Mapping[str, int | float | str | None]) -> SDRowIdent:
        return tuple(row[k] for k in self.key_columns if k in row)

    def add_row(self, ident: SDRowIdent, row: Mapping[str, int | float | str | None]) -> None:
        if row:
            self._rows.setdefault(ident, {}).update(row)

    def get_row(self, row: SDRow) -> SDRow:
        ident = self._make_row_ident(row)
        if ident in self.retentions:
            return {k: row[k] for k in self.retentions[ident] if k in row}
        return row

    #   ---retentions-----------------------------------------------------------

    def update_from_previous(  # pylint: disable=too-many-branches
        self,
        now: int,
        other: object,
        filter_func: SDFilterFunc,
        inv_intervals: RetentionIntervals,
        path: SDPath,
    ) -> UpdateResult:
        if not isinstance(other, Table):
            raise TypeError(f"Cannot update {type(self)} from {type(other)}")

        self.add_key_columns(other.key_columns)

        old_filtered_rows = {
            ident: filtered_row
            for ident, row in other._rows.items()
            if (
                filtered_row := _get_filtered_dict(
                    row,
                    _make_retentions_filter_func(
                        filter_func=filter_func,
                        intervals_by_keys=other.retentions.get(ident),
                        now=now,
                    ),
                )
            )
        }
        self_filtered_rows = {
            ident: filtered_row
            for ident, row in self._rows.items()
            if (filtered_row := _get_filtered_dict(row, filter_func))
        }
        compared_filtered_idents = _compare_dict_keys(
            old_dict=old_filtered_rows,
            new_dict=self_filtered_rows,
        )

        retentions: TableRetentions = {}
        update_result = UpdateResult()
        for ident in compared_filtered_idents.only_old:
            old_row: SDRow = {}
            for key, value in old_filtered_rows[ident].items():
                old_row.setdefault(key, value)
                retentions.setdefault(ident, {})[key] = other.retentions[ident][key]

            if old_row:
                # Update row with key column entries
                old_row.update({k: other._rows[ident][k] for k in other.key_columns})
                self.add_row(ident, old_row)
                update_result.add_row_reason(path, ident, "row", old_row)

        for ident in compared_filtered_idents.both:
            compared_filtered_keys = _compare_dict_keys(
                old_dict=old_filtered_rows[ident],
                new_dict=self_filtered_rows[ident],
            )
            row: SDRow = {}
            for key in compared_filtered_keys.only_old:
                row.setdefault(key, other._rows[ident][key])
                retentions.setdefault(ident, {})[key] = other.retentions[ident][key]

            for key in compared_filtered_keys.both.union(compared_filtered_keys.only_new):
                retentions.setdefault(ident, {})[key] = inv_intervals

            if row:
                # Update row with key column entries
                row.update(
                    {
                        **{k: other._rows[ident][k] for k in other.key_columns},
                        **{k: self._rows[ident][k] for k in self.key_columns},
                    }
                )
                self.add_row(ident, row)
                update_result.add_row_reason(path, ident, "row", row)

        for ident in compared_filtered_idents.only_new:
            for key in self_filtered_rows[ident]:
                retentions.setdefault(ident, {})[key] = inv_intervals

        if retentions:
            self.set_retentions(retentions)
            for ident, intervals in retentions.items():
                update_result.add_row_reason(path, ident, "intervals", intervals)

        return update_result

    def set_retentions(self, table_retentions: TableRetentions) -> None:
        self.retentions = table_retentions

    def get_retention_intervals(self, key: SDKey, row: SDRow) -> RetentionIntervals | None:
        return self.retentions.get(self._make_row_ident(row), {}).get(key)

    #   ---representation-------------------------------------------------------

    def __repr__(self) -> str:
        # Only used for repr/debug purposes
        return f"{self.__class__.__name__}({pprint.pformat(self.serialize())})"

    #   ---de/serializing-------------------------------------------------------

    def serialize(self) -> SDRawTree:
        raw_table = {}
        if self._rows:
            raw_table.update(
                {
                    _KEY_COLUMNS_KEY: self.key_columns,
                    _ROWS_KEY: list(self._rows.values()),
                }
            )

        if self.retentions:
            raw_table[_RETENTIONS_KEY] = {
                ident: _serialize_retentions(intervals)
                for ident, intervals in self.retentions.items()
            }
        return raw_table

    @classmethod
    def deserialize(cls, *, raw_rows: SDRawTree) -> Table:
        rows = raw_rows.get(_ROWS_KEY, [])
        if _KEY_COLUMNS_KEY in raw_rows:
            key_columns = raw_rows[_KEY_COLUMNS_KEY]
        else:
            key_columns = cls._get_default_key_columns(rows)

        table = cls(
            key_columns=key_columns,
            retentions={
                ident: _deserialize_retentions(raw_intervals)
                for ident, raw_intervals in raw_rows.get(_RETENTIONS_KEY, {}).items()
            },
        )
        table.add_rows(rows)
        return table

    @classmethod
    def _deserialize_legacy(cls, *, legacy_rows: LegacyRows) -> Table:
        table = cls(key_columns=cls._get_default_key_columns(legacy_rows))
        table.add_rows(legacy_rows)
        return table

    @staticmethod
    def _get_default_key_columns(rows: list[SDRow]) -> SDKeyColumns:
        return sorted({k for r in rows for k in r})


class Attributes:
    def __init__(
        self,
        *,
        retentions: RetentionIntervalsByKeys | None = None,
    ) -> None:
        self.retentions = retentions if retentions else {}
        self.pairs: SDPairs = {}

    #   ---common methods-------------------------------------------------------

    def __bool__(self) -> bool:
        return bool(self.pairs)

    def is_equal(self, other: object) -> bool:
        if not isinstance(other, Attributes):
            raise TypeError(f"Cannot compare {type(self)} with {type(other)}")

        return self.pairs == other.pairs

    def count_entries(self) -> int:
        return len(self.pairs)

    #   ---attributes methods---------------------------------------------------

    def add_pairs(self, pairs: SDPairs | SDPairsFromPlugins) -> None:
        self.pairs.update(pairs)

    #   ---retentions-----------------------------------------------------------

    def update_from_previous(
        self,
        now: int,
        other: object,
        filter_func: SDFilterFunc,
        inv_intervals: RetentionIntervals,
        path: SDPath,
    ) -> UpdateResult:
        if not isinstance(other, Attributes):
            raise TypeError(f"Cannot update {type(self)} from {type(other)}")

        compared_filtered_keys = _compare_dict_keys(
            old_dict=_get_filtered_dict(
                other.pairs,
                _make_retentions_filter_func(
                    filter_func=filter_func,
                    intervals_by_keys=other.retentions,
                    now=now,
                ),
            ),
            new_dict=_get_filtered_dict(self.pairs, filter_func),
        )

        pairs: SDPairs = {}
        retentions: RetentionIntervalsByKeys = {}
        for key in compared_filtered_keys.only_old:
            pairs.setdefault(key, other.pairs[key])
            retentions[key] = other.retentions[key]

        for key in compared_filtered_keys.both.union(compared_filtered_keys.only_new):
            retentions[key] = inv_intervals

        update_result = UpdateResult()
        if pairs:
            self.add_pairs(pairs)
            update_result.add_attr_reason(path, "pairs", pairs)

        if retentions:
            self.set_retentions(retentions)
            update_result.add_attr_reason(path, "intervals", retentions)

        return update_result

    def set_retentions(self, intervals_by_keys: RetentionIntervalsByKeys) -> None:
        self.retentions = intervals_by_keys

    def get_retention_intervals(self, key: SDKey) -> RetentionIntervals | None:
        return self.retentions.get(key)

    #   ---representation-------------------------------------------------------

    def __repr__(self) -> str:
        # Only used for repr/debug purposes
        return f"{self.__class__.__name__}({pprint.pformat(self.serialize())})"

    #   ---de/serializing-------------------------------------------------------

    def serialize(self) -> SDRawTree:
        raw_attributes = {}
        if self.pairs:
            raw_attributes[_PAIRS_KEY] = self.pairs

        if self.retentions:
            raw_attributes[_RETENTIONS_KEY] = _serialize_retentions(self.retentions)
        return raw_attributes

    @classmethod
    def deserialize(cls, *, raw_pairs: SDRawTree) -> Attributes:
        attributes = cls(retentions=_deserialize_retentions(raw_pairs.get(_RETENTIONS_KEY)))
        attributes.add_pairs(raw_pairs.get(_PAIRS_KEY, {}))
        return attributes

    @classmethod
    def _deserialize_legacy(cls, *, legacy_pairs: LegacyPairs) -> Attributes:
        attributes = cls()
        attributes.add_pairs(legacy_pairs)
        return attributes


# .
#   .--delta tree----------------------------------------------------------.
#   |                  _      _ _          _                               |
#   |               __| | ___| | |_ __ _  | |_ _ __ ___  ___               |
#   |              / _` |/ _ \ | __/ _` | | __| '__/ _ \/ _ \              |
#   |             | (_| |  __/ | || (_| | | |_| | |  __/  __/              |
#   |              \__,_|\___|_|\__\__,_|  \__|_|  \___|\___|              |
#   |                                                                      |
#   '----------------------------------------------------------------------'


_SDEncodeAs = Callable[[SDValue], tuple[SDValue | None, SDValue | None]]
_SDDeltaCounter = Counter[Literal["new", "changed", "removed"]]


def _merge_delta_attributes(left: DeltaAttributes, right: DeltaAttributes) -> DeltaAttributes:
    return DeltaAttributes(pairs={**left.pairs, **right.pairs})


def _merge_delta_table(left: DeltaTable, right: DeltaTable) -> DeltaTable:
    delta_key_columns = []
    for key_column in left.key_columns:
        if key_column not in delta_key_columns:
            delta_key_columns.append(key_column)
    for key_column in right.key_columns:
        if key_column not in delta_key_columns:
            delta_key_columns.append(key_column)

    delta_rows = []
    for row in left.rows:
        if row not in delta_rows:
            delta_rows.append(row)
    for row in right.rows:
        if row not in delta_rows:
            delta_rows.append(row)

    return DeltaTable(key_columns=delta_key_columns, rows=delta_rows)


def _merge_delta_nodes(
    left: DeltaStructuredDataNode, right: DeltaStructuredDataNode
) -> DeltaStructuredDataNode:
    delta_nodes = {}

    compared_keys = _compare_dict_keys(
        old_dict=left.nodes_by_name,
        new_dict=right.nodes_by_name,
    )

    for key in compared_keys.only_old:
        delta_nodes[key] = left.nodes_by_name[key]

    for key in compared_keys.both:
        delta_nodes[key] = _merge_delta_nodes(
            left.nodes_by_name[key],
            right.nodes_by_name[key],
        )

    for key in compared_keys.only_new:
        delta_nodes[key] = right.nodes_by_name[key]

    return DeltaStructuredDataNode(
        path=left.path,
        attributes=_merge_delta_attributes(left.attributes, right.attributes),
        table=_merge_delta_table(left.table, right.table),
        _nodes=delta_nodes,
    )


def _count_dict_entries(dict_: dict[SDKey, tuple[SDValue, SDValue]]) -> _SDDeltaCounter:
    counter: _SDDeltaCounter = Counter()
    for value0, value1 in dict_.values():
        match [value0 is None, value1 is None]:
            case [True, False]:
                counter["new"] += 1
            case [False, True]:
                counter["removed"] += 1
            case [False, False] if value0 != value1:
                counter["changed"] += 1
    return counter


@dataclass(frozen=True)
class DeltaStructuredDataNode:
    path: SDPath
    attributes: DeltaAttributes
    table: DeltaTable
    _nodes: dict[SDNodeName, DeltaStructuredDataNode]

    @classmethod
    def make_from_node(
        cls, *, node: StructuredDataNode, encode_as: _SDEncodeAs
    ) -> DeltaStructuredDataNode:
        return cls(
            path=node.path,
            attributes=DeltaAttributes.make_from_attributes(
                attributes=node.attributes,
                encode_as=encode_as,
            ),
            table=DeltaTable.make_from_table(
                table=node.table,
                encode_as=encode_as,
            ),
            _nodes={
                name: cls.make_from_node(
                    node=child,
                    encode_as=encode_as,
                )
                for name, child in node.nodes_by_name.items()
            },
        )

    def __bool__(self) -> bool:
        if self.attributes or self.table:
            return True

        for node in self._nodes.values():
            if node:
                return True

        return False

    def add_node(self, path: SDPath, node: DeltaStructuredDataNode) -> None:
        if not path:
            return

        node_name = path[0]
        node_path = self.path + (path[0],)
        if len(path) == 1:
            if node_name in self._nodes:
                merge_node = self._nodes[node_name]
            else:
                merge_node = DeltaStructuredDataNode(
                    path=node_path,
                    attributes=DeltaAttributes(pairs={}),
                    table=DeltaTable(key_columns=[], rows=[]),
                    _nodes={},
                )
            self._nodes[node_name] = _merge_delta_nodes(merge_node, node)
            return

        self._nodes.setdefault(
            node_name,
            DeltaStructuredDataNode(
                path=node_path,
                attributes=DeltaAttributes(pairs={}),
                table=DeltaTable(key_columns=[], rows=[]),
                _nodes={},
            ),
        ).add_node(path[1:], node)

    def get_node(self, path: SDPath) -> DeltaStructuredDataNode | None:
        if not path:
            return self
        node = self._nodes.get(path[0])
        return None if node is None else node.get_node(path[1:])

    @property
    def nodes(self) -> Iterator[DeltaStructuredDataNode]:
        yield from self._nodes.values()

    @property
    def nodes_by_name(self) -> Mapping[SDNodeName, DeltaStructuredDataNode]:
        return self._nodes

    def serialize(self) -> SDRawDeltaTree:
        return {
            "Attributes": self.attributes.serialize(),
            "Table": self.table.serialize(),
            "Nodes": {edge: node.serialize() for edge, node in self._nodes.items()},
        }

    @classmethod
    def deserialize(cls, raw_delta_tree: object) -> DeltaStructuredDataNode:
        return cls._deserialize(path=tuple(), raw_delta_tree=raw_delta_tree)

    @classmethod
    def _deserialize(cls, *, path: SDPath, raw_delta_tree: object) -> DeltaStructuredDataNode:
        if not isinstance(raw_delta_tree, dict):
            raise TypeError()
        return cls(
            path=path,
            attributes=DeltaAttributes.deserialize(
                raw_delta_attributes=raw_delta_tree.get("Attributes", {})
            ),
            table=DeltaTable.deserialize(raw_delta_table=raw_delta_tree.get("Table", {})),
            _nodes={
                raw_node_name: cls._deserialize(
                    path=path + (raw_node_name,),
                    raw_delta_tree=raw_node,
                )
                for raw_node_name, raw_node in raw_delta_tree.get("Nodes", {}).items()
            },
        )

    def count_entries(self) -> _SDDeltaCounter:
        counter: _SDDeltaCounter = Counter()
        counter.update(self.attributes.count_entries())
        counter.update(self.table.count_entries())
        for node in self._nodes.values():
            counter.update(node.count_entries())
        return counter


@dataclass(frozen=True)
class DeltaTable:
    key_columns: list[SDKey]
    rows: list[dict[SDKey, tuple[SDValue, SDValue]]]

    @classmethod
    def make_from_table(cls, *, table: Table, encode_as: _SDEncodeAs) -> DeltaTable:
        return cls(
            key_columns=table.key_columns,
            rows=[{key: encode_as(value) for key, value in row.items()} for row in table.rows],
        )

    def __bool__(self) -> bool:
        return bool(self.rows)

    def serialize(self) -> SDRawDeltaTree:
        return {"KeyColumns": self.key_columns, "Rows": self.rows} if self.rows else {}

    @classmethod
    def deserialize(cls, *, raw_delta_table: object) -> DeltaTable:
        if not isinstance(raw_delta_table, dict):
            raise TypeError()
        return cls(
            key_columns=raw_delta_table.get("KeyColumns", []),
            rows=raw_delta_table.get("Rows", []),
        )

    def count_entries(self) -> _SDDeltaCounter:
        counter: _SDDeltaCounter = Counter()
        for row in self.rows:
            counter.update(_count_dict_entries(row))
        return counter


@dataclass(frozen=True)
class DeltaAttributes:
    pairs: dict[SDKey, tuple[SDValue, SDValue]]

    @classmethod
    def make_from_attributes(
        cls, *, attributes: Attributes, encode_as: _SDEncodeAs
    ) -> DeltaAttributes:
        return cls(pairs={key: encode_as(value) for key, value in attributes.pairs.items()})

    def __bool__(self) -> bool:
        return bool(self.pairs)

    def serialize(self) -> SDRawDeltaTree:
        return {"Pairs": self.pairs} if self.pairs else {}

    @classmethod
    def deserialize(cls, *, raw_delta_attributes: object) -> DeltaAttributes:
        if not isinstance(raw_delta_attributes, dict):
            raise TypeError()
        return cls(pairs=raw_delta_attributes.get("Pairs", {}))

    def count_entries(self) -> _SDDeltaCounter:
        return _count_dict_entries(self.pairs)


# .
#   .--helpers-------------------------------------------------------------.
#   |                  _          _                                        |
#   |                 | |__   ___| |_ __   ___ _ __ ___                    |
#   |                 | '_ \ / _ \ | '_ \ / _ \ '__/ __|                   |
#   |                 | | | |  __/ | |_) |  __/ |  \__ \                   |
#   |                 |_| |_|\___|_| .__/ \___|_|  |___/                   |
#   |                              |_|                                     |
#   '----------------------------------------------------------------------'


class ComparedDictKeys(NamedTuple):
    only_old: set
    both: set
    only_new: set


def _compare_dict_keys(*, old_dict: Mapping, new_dict: Mapping) -> ComparedDictKeys:
    """
    Returns the set relationships of the keys between two dictionaries:
    - relative complement of new_dict in old_dict
    - intersection of both
    - relative complement of old_dict in new_dict
    """
    old_keys, new_keys = set(old_dict), set(new_dict)
    return ComparedDictKeys(
        only_old=old_keys - new_keys,
        both=old_keys.intersection(new_keys),
        only_new=new_keys - old_keys,
    )


def _make_retentions_filter_func(
    *,
    filter_func: SDFilterFunc,
    intervals_by_keys: RetentionIntervalsByKeys | None,
    now: int,
) -> SDFilterFunc:
    return lambda k: bool(
        filter_func(k)
        and intervals_by_keys
        and (intervals := intervals_by_keys.get(k))
        and now <= intervals.keep_until
    )


def _get_filtered_dict(dict_: dict, filter_func: SDFilterFunc) -> dict:
    return {k: v for k, v in dict_.items() if filter_func(k)}


def _serialize_retentions(
    intervals_by_keys: RetentionIntervalsByKeys,
) -> RawRetentionIntervalsByKeys:
    return {key: intervals.serialize() for key, intervals in intervals_by_keys.items()}


def _deserialize_retentions(
    raw_intervals_by_keys: RawRetentionIntervalsByKeys | None,
) -> RetentionIntervalsByKeys:
    if not raw_intervals_by_keys:
        return {}
    return {
        key: RetentionIntervals.deserialize(intervals)
        for key, intervals in raw_intervals_by_keys.items()
    }
