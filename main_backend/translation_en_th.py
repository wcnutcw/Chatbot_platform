from deep_translator import GoogleTranslator

def detect_language_str(word):
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
        return "mixed"
    else:
        return "other"
    
def detect_language_list(word):
    is_thai = False
    is_english = False

    # ถ้า input เป็น list ให้รวมเป็น string ก่อน
    if isinstance(word, list):
        word = " ".join(word)

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
        return "mix"
    else:
        return "other"

    
def translation_en_2_th(text, source='en', target='th'):
    result=GoogleTranslator(source=source, target=target).translate(text)
    print(f"translation : {result}")
    return result

def translation_th_2_eng(text, source='th', target='en'):
    result=GoogleTranslator(source=source, target=target).translate(text)
    print(f"translation : {result}")
    return result
