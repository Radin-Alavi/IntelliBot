from deep_translator import GoogleTranslator
def translate(text, origin, destination):
    translated = GoogleTranslator(source=origin, target=destination).translate(text)
    print(translated)
    return translated