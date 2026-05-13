"""Stdlib-backed pyjson5 shim used by the vendored PyMarkdown tree.

PyMarkdown's `application_properties` dependency imports pyjson5 at module
load time. The upstream pyjson5 ships as a C extension; vendoring it would
bake one platform's compiled artifact into the skill bundle. The
PyMarkdown CLI is always invoked with --no-json5, so the
`load_json_files_as_json5` code paths in application_properties never run.
This shim therefore only satisfies the imports and the exception symbols
those modules reference. Calling load/loads raises so misuse is loud.
"""


class Json5EOF(Exception):
    pass


class Json5DecoderException(Exception):
    pass


def _unavailable(*_args, **_kwargs):
    raise RuntimeError(
        "vendored pyjson5 shim: JSON5 support is not bundled; "
        "invoke pymarkdown with --no-json5"
    )


load = _unavailable
loads = _unavailable
dump = _unavailable
dumps = _unavailable
