from collections import OrderedDict, Mapping

from wildpath.paths import WildPath

_marker = object()


class PathCollector(object):

    def __init__(self, collect_tuples, default=_marker):
        self.default = default
        self.key_paths = OrderedDict()
        self.encoders = {}
        for tpl in collect_tuples:
            key = tpl[0]
            self.key_paths[key] = WildPath(tpl[1])
            self.encoders[key] = tpl[2] if len(tpl) > 2 else lambda v: v
        self._check_paths(self.key_paths.values())

    def _stripped_path(self, path):
        stripped = path[:]
        for key in reversed(path):
            if key in WildPath._preprocessed:
                break
            stripped = stripped[:-1]
        return stripped

    def _check_paths(self, paths):
        if not len(paths):
            raise ValueError("'PathCollector' cannot collect with no paths")
        stripped_paths = [self._stripped_path(p) for p in paths]
        stripped_paths = sorted(stripped_paths, key=lambda p: len(p))
        check_path = WildPath()
        for path in stripped_paths:
            if path[:len(check_path)] != check_path:
                raise ValueError("paths in 'PathCollector' must be identical left of rightmost wildcard key")
            check_path = path

    def _split_path(self, path):
        for i, key in enumerate(path):
            if key in WildPath._preprocessed:
                return path[:i], path[i:i + 1], path[i + 1:]
        return path, (), ()

    def __call__(self, source):
        split_path = self._split_path
        encoders = self.encoders
        default = self.default

        def listify(iterable):
            if isinstance(iterable, Mapping):
                return iterable.values()
            return iterable

        def reduce(key_paths, source, target):
            sub_key_paths = {}
            sub_sources = None
            for key, path in key_paths.items():
                base_path, wild_path, sub_path = split_path(path)
                if default is _marker:
                    new_source = base_path.get_in(source)
                else:
                    new_source = base_path.get_in(source, default)
                if len(wild_path):
                    if not sub_sources:
                        sub_sources = listify(wild_path.get_in(new_source))
                    sub_key_paths[key] = sub_path
                else:
                    target[key] = encoders[key](new_source)

            if sub_sources:
                targets = []
                for sub_source in sub_sources:
                    targets.extend(reduce(sub_key_paths, sub_source, target.copy()))
                return targets
            else:
                return [target]

        return reduce(self.key_paths, source, OrderedDict((k, None) for k in self.key_paths))


