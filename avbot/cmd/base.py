from avbot.i18n import _, __

COUNTRIES = {
    "ru": __("Russia"),
    "su": __("Soviet Union"),
    "us": __("United States"),
}


class PlateRequestBase:
    num_type = None
    example = None
    description = None
    task = None

    @classmethod
    def validate(cls, query):
        raise NotImplementedError()

    @classmethod
    def search(cls, validated_query):
        raise NotImplementedError()

    @classmethod
    def msg_no_data(cls):
        return _("No data")

    @classmethod
    def msg_no_results(cls, validated_query):
        return _("Nothing found")

    @classmethod
    def msg_with_results(cls, validated_query, result):
        raise NotImplementedError()


def translate_to_latin(text):
    chars = ("авекмнорстухАВЕКМНОРСТУХ", "abekmhopctyxabekmhopctyx")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def translate_to_cyr(text):
    chars = ("iI", "\u0456\u0406")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def translate_to_cyrillic(number):
    chars = ("abekmhopctyx", "АВЕКМНОРСТУХ")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return number.translate(table)
