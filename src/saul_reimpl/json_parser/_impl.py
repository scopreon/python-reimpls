from __future__ import annotations
from typing import Any, Generator, Never, Iterator, cast, overload
import json
from enum import Enum, auto
from dataclasses import dataclass

type JsonObject = (
    list[JsonObject] | dict[str, JsonObject] | int | str | float | bool | None
)


def error() -> Never:
    raise RuntimeError("")


class JsonTokenType(Enum):
    e_STRING = auto()
    e_NUMBER = auto()
    e_SYMBOL = auto()
    e_BOOL = auto()
    e_NULL = auto()


@dataclass()
class JsonToken:
    type: JsonTokenType
    value: str | int | float | str | bool | None

    def __post_init__(self) -> None:
        type_to_enum: dict[type, tuple[JsonTokenType, ...]] = {
            str: (JsonTokenType.e_STRING, JsonTokenType.e_SYMBOL),
            int: (JsonTokenType.e_NUMBER,),
            float: (JsonTokenType.e_NUMBER,),
            type(None): (JsonTokenType.e_NULL,),
            bool: (JsonTokenType.e_BOOL,),
        }
        assert self.type in type_to_enum[type(self.value)]


def _is_low_surrogate(val: int) -> bool:
    return 0xDC00 <= val <= 0xDFFF


def _is_high_surrogate(val: int) -> bool:
    return 0xD800 <= val <= 0xDBFF


class JsonTokeniser:
    _pointer: int = 0
    _string: str

    def _read_spaces(self) -> None:
        while self._char() == " " or self._char() == "\n":
            self._pointer += 1

    def _char(self) -> str:
        return self._word(1)

    def _eof(self) -> bool:
        return self._pointer == len(self._string)

    def _increment(self, count: int = 1) -> None:
        self._pointer += count

    def _word(self, length: int) -> str:
        if self._pointer > len(self._string):
            error()
        return self._string[self._pointer : self._pointer + length]

    def _read_string(self) -> str:
        s = ""
        escape = False
        while escape or self._char() != '"':
            if escape:
                if self._char() == "\\":
                    s += "\\"
                elif self._char() == "n":
                    s += "\n"
                elif self._char() == "b":
                    s += "\b"
                elif self._char() == "t":
                    s += "\t"
                elif self._char() == '"':
                    s += '"'
                elif self._char() == "r":
                    s += "\r"
                elif self._char() == "f":
                    s += "\f"
                elif self._char() == "/":
                    s += "/"
                elif self._char() == "u":
                    self._increment()
                    high = int(self._word(4), 16)
                    self._increment(3)
                    if _is_high_surrogate(high):
                        self._increment()  # previous last digit
                        self._increment(2)  # \u
                        low = int(self._word(4), 16)
                        self._increment(3)
                        if not _is_low_surrogate(low):
                            error()
                        # 2**16 + 2**10*(H - 0xD800) + L - 0xDC00 == 0x1F680
                        s += chr(
                            pow(2, 16) + pow(2, 10) * (high - 0xD800) + low - 0xDC00
                        )
                    else:
                        s += chr(high)
                else:
                    error()
                escape = False
            else:
                if self._char() == "\\":
                    escape = True
                else:
                    s += self._char()

            self._increment()
        return s

    def _read_alpha_word(self) -> str:
        s = ""
        while (c := self._char()).isalpha():
            s += c
        return s

    def _read_number(self) -> int | float:
        is_negative = False
        number = 0

        if not self._eof() and self._char() == "-":
            is_negative = True
            self._increment()

        while not self._eof() and (c := self._char()).isdigit():
            number *= 10
            number += int(c)
            self._increment()

        if not self._eof() and self._char() == ".":
            self._increment()
            fraction = 0
            count = 0
            while (c := self._char()).isdigit():
                count += 1
                fraction += int(c) / pow(10, count)
                self._increment()
            number += fraction

        if not self._eof() and self._char() in "eE":
            mult = 0
            positive = True
            self._increment()
            if self._char() == "-":
                positive = False
                self._increment()
            if self._char() == "+":
                self._increment()

            while (c := self._char()).isdigit():
                mult *= 10
                mult += int(c)
                if number == 0:
                    break
                self._increment()

            if positive:
                number *= pow(10, mult)
            else:
                number *= pow(10, -mult)

        if is_negative:
            return -1 * number

        return float(number) if not number.is_integer() else int(number)

    def tokenise(self, string: str) -> list[JsonToken]:
        self._string = string
        tokens = []
        try:
            while self._pointer < len(self._string):
                self._read_spaces()
                if self._pointer == len(self._string):
                    break
                if self._char() in ["{", "}", "[", "]", ",", ":"]:
                    tokens.append(JsonToken(JsonTokenType.e_SYMBOL, self._char()))
                    self._increment()
                elif self._char() == '"':
                    self._increment()  # "
                    tokens.append(
                        JsonToken(JsonTokenType.e_STRING, self._read_string())
                    )
                    self._increment()  # "
                elif self._char() == "-" or self._char().isdigit():
                    tokens.append(
                        JsonToken(JsonTokenType.e_NUMBER, self._read_number())
                    )
                elif self._word(5) == "false":
                    tokens.append(JsonToken(JsonTokenType.e_BOOL, False))
                    self._increment(5)
                elif self._word(4) == "true":
                    tokens.append(JsonToken(JsonTokenType.e_BOOL, True))
                    self._increment(4)
                elif self._word(4) == "null":
                    tokens.append(JsonToken(JsonTokenType.e_NULL, None))
                    self._increment(4)
                else:
                    error()
        except Exception:
            print(self._string[self._pointer :])
            raise

        return tokens


class JsonParser:
    _tokens: Iterator[JsonToken]

    def _token(self) -> JsonToken:
        return next(self._tokens)

    def _process_dict(self) -> dict[str, JsonObject]:
        ret: dict[str, JsonObject] = {}
        anticipate = False
        token = self._token()
        while not (
            token.type == JsonTokenType.e_SYMBOL
            and token.value == "}"
            and not anticipate
        ):
            if token.type != JsonTokenType.e_STRING:
                error()
            key = token
            token = self._token()

            if not (token.type == JsonTokenType.e_SYMBOL and token.value == ":"):
                error()
            token = self._token()
            ret[cast(str, key.value)] = self._parse_json_object(token)
            token = self._token()
            if token.type == JsonTokenType.e_SYMBOL and token.value == ",":
                anticipate = True
                token = self._token()
            else:
                anticipate = False
        return ret

    def _process_list(self) -> list[JsonObject]:
        ret = []
        anticipate = False
        token = self._token()
        while not (
            token.type == JsonTokenType.e_SYMBOL
            and token.value == "]"
            and not anticipate
        ):
            ret.append(self._parse_json_object(token))

            token = self._token()
            if token.type == JsonTokenType.e_SYMBOL and token.value == ",":
                anticipate = True
                token = self._token()
            else:
                anticipate = False
        return ret

    def _parse_json_object(self, token: JsonToken) -> JsonObject:
        if token.type == JsonTokenType.e_SYMBOL and token.value == "[":
            return self._process_list()
        elif token.type == JsonTokenType.e_SYMBOL and token.value == "{":
            return self._process_dict()
        elif token.type == JsonTokenType.e_SYMBOL:
            error()
        else:
            return token.value

    def parse(self, string: str) -> JsonObject:
        try:
            tokeniser = JsonTokeniser()
            self._tokens = iter(tokeniser.tokenise(string))
            ret: JsonObject
            token = self._token()
            ret = self._parse_json_object(token)
            try:
                self._token()
            except StopIteration:
                return ret
            error()
        except:
            for i in self._tokens:
                print(i)
            raise


# def text_to_json(string: str) -> dict[Any, Any]:
#     obj = {}
#     return obj


# a = JsonParser()
# print(a.parse('{"test": 123, "hello": [1,2,3,4]}'))
a = JsonParser()


def check(s: str) -> None:
    assert a.parse(s) == json.loads(s), f"Mismatch for: {s}"


# 🔥 STRING TESTS
check(r'"\\\\"')
check(r'"\\/\\"')
check(r'"\b\f\n\r\t"')

# 🔥 UNICODE (VALID ONLY)
check(r'"\u0041"')
check(r'"\u03A9"')
check(r'"\uD834\uDD1E"')
check(r'"\uFFFF"')

# 🔥 NUMBERS (VALID)
check(r"0")
check(r"-0")
check(r"0.0")
check(r"-0.0")
check(r"1e10")
check(r"1E-10")
check(r"-1.23e+45")
check(r"123456789")

# 🔥 ARRAYS
check(r"[1,2,3]")
check(r"[ 1 , 2 , 3 ]")
check(r"[]")
check(r"[[]]")
check(r"[{},[]]")
check(r"[1,[2,[3,[4]]]]")

# 🔥 OBJECTS
check(r"{}")
check(r'{"a":1}')
check(r'{"a":1,"b":2}')
check(r'{ "a" : 1 }')
check(r'{"a":1 , "b" :2}')
check(r'{"":1}')
check(r'{" ":2}')
check(r'{"a":{}}')
check(r'{"a":[]}')

# 🔥 NESTED STRUCTURES
check(r'{"a":{"b":{"c":3}}}')
check(r'{"x":[1,{"y":[2,3]},4]}')
check(r'{"a":[{"b":1},{"c":2}]}')
check(r'{"a":[1,{"b":[2,{"c":[3,4,{"d":5}]}]}]}')

# 🔥 LITERALS
check(r"true")
check(r"false")
check(r"null")

# 🔥 MIXED REALISTIC
check(r'{"users":[{"id":1,"name":"a"},{"id":2,"name":"b"}]}')

# 🔥 WHITESPACE
# check(r'\n\t { \r "a" \n : \t 1 \r } \n')

# 🔥 STRING EDGE CASES
check(r'""')
check(r'" "')
check(r'"\u0000"')
check(r'"end\n"')

# 🔥 LARGE OBJECT
big_obj = r"{" + ",".join([f'"k{i}":{i}' for i in range(50)]) + r"}"
check(big_obj)

# 🔥 LARGE ARRAY
big_arr = r"[" + ",".join(str(i) for i in range(200)) + r"]"
check(big_arr)

# 🔥 COMBINED LARGE STRUCTURE
combo = r'{"data":' + big_obj + r',"arr":' + big_arr + r"}"
check(combo)

# 🔥 DEEP (reasonable depth, should still pass)
deep = r"[" * 200 + r"0" + r"]" * 200
check(deep)

deep_obj = (r'{"a":' * 100) + r"0" + (r"}" * 100)
check(deep_obj)

# 💣 FINAL COMPLEX VALID JSON
ultimate1 = r"""
{
  "a": [1, -2.3e+4, true, false, null, {"nested": ["\u0041", "\n", "\\"]}],
  "b": {"deep": {"x": {"y": {"z": [0,1,2,3,{"k":"v"}]}}}},
  "c": "A long string with escapes \n \t \u03A9 and quotes \" inside",
  "d": []
}
"""
check(ultimate1)

ultimate2 = r"""
{
  "quote": "He said, \"Hello, world!\"",
  "backslash": "This is a backslash: \\",
  "slash": "Forward slash: /",
  "newline": "Line1\nLine2",
  "tab": "Column1\tColumn2",
  "carriage_return": "First line\rSecond line",
  "backspace": "ABC\bDEF",
  "formfeed": "Page1\fPage2",
  "unicode": "Snowman: \u2603, Emoji: \uD83D\uDE03",
  "mixed": "Quotes: \" \\ \/ \b \f \n \r \t and unicode \u2764",
  "nested": {
    "array": ["One\nTwo", "Tab\tHere", "Quote: \"", "Slash\\/Backslash\\\\"]
  }
}
"""
check(ultimate2)

print("All tests passed!")
