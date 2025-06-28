from googletrans import Translator

def detect_language(word):
    is_thai = False
    is_english = False

    for ch in word:
        if '\u0E00' <= ch <= '\u0E7F':
            is_thai = True
        elif ('A' <= ch <= 'Z') or ('a' <= ch <= 'z'):
            is_english = True

    if is_thai and not is_english:
        return "thai"
    elif is_english and not is_thai:
        return "english"
    elif is_thai and is_english:
        return "thai"
    else:
        return "other"
    
def translation(text):
    translator = Translator()
    result = translator.translate(text, src="th", dest="en")
    print(f"translation : {result.text}")
    return result.text
