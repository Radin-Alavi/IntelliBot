from translate import Translator
def translate(text, origin, destination):
    translator = Translator(destination)
    translated_text = translator.translate(text)
    print(translated_text)
    return translated_text
