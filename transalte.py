from translate import Translator
dest = input("Enter the destination:")
translator = Translator(dest)
origin = input(translator.translate("Enter text:"))
result = translator.translate(origin)

print(result)
