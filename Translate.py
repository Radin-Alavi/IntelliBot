from translate import Translator

origin = input("Enter text:")

dest = input("Enter the destination:")
translator = Translator(dest)
result = translator.translate(origin)

print(result)
