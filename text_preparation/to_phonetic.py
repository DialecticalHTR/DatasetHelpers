import re
import unicodedata
from string import *
from pathlib import Path

from russian_g2p.Accentor import Accentor


# Useful constants
HARD_VOWELS = 'аоуыэАОУЫЭ'
SOFT_VOWELS = 'яёюиеЯЁЮИЕ'
VOWELS = HARD_VOWELS + SOFT_VOWELS

PAIRED_CONSONANTS = 'бвгдзклмнпрстфхБВГДЗКЛМНПРСТФХ'
ALWAYS_SOFT_CONSONANTS = 'чщйЧЩЙ'
ALWAYS_HARD_CONSONANTS = 'жшцЖШЦ'
CONSONANTS = PAIRED_CONSONANTS + ALWAYS_SOFT_CONSONANTS + ALWAYS_HARD_CONSONANTS

RUSSIAN_ALPHABET = CONSONANTS + VOWELS + 'ьъЬЪ'

COMBINING_ACUTE = '\u0301'
APOSTROPHE = '\u0027'


accentor = Accentor()


def decompose_acutes(text: str) -> str:
    result = ""
    for char in text:
        decomposed = unicodedata.normalize('NFD', char) 
        if COMBINING_ACUTE in decomposed:
            result += decomposed
        else:
            result += char 
    return result


# def add_accents(text: str) -> str:
#     normalized = decompose_acutes(text)
#     words = normalized.split()

#     result = []
#     for word in words:
#         if COMBINING_ACUTE not in word:
#             word = filter_not_alnum(word)
#             if not word:
#                 continue
#             word = accentor.do_accents([[word]])[0][0]
#             word = word.replace('+', COMBINING_ACUTE)
#         result.append(word)

#     return ' '.join(result)


def add_accents(text: str) -> str:
    normalized = decompose_acutes(text)

    # Filter all non-word symbols
    words = set()
    alphabet = RUSSIAN_ALPHABET + ascii_letters + digits + '-'
    for word in normalized.split():
        word = ''.join(filter(lambda c: c in alphabet, word))
        if word:
            words.add(word)
    words = list(words)

    to_accent = [[word] for word in words]
    accent_data = accentor.do_accents(to_accent)
    accented = [word.replace('+', COMBINING_ACUTE) for word in accent_data[0]]

    for word, accented_word in zip(words, accented):
        text = text.replace(word, accented_word)
    return text


def add_softness(text: str) -> str:
    result = text[0]
    for i in range(1, len(text)):
        previous, current = text[i-1], text[i]

        if current in SOFT_VOWELS and previous in PAIRED_CONSONANTS:
            result += APOSTROPHE
        result += current

    return result


def add_pauses(text: str) -> str: 
    short_pauses = text.translate(
        {ord(c): ' / ' for c in ','}
    )
    
    sentences = re.split('[\?\!\.]+', short_pauses)
    sentences = [' '.join(sentence.split()) for sentence in sentences]
    sentences = [sentence.capitalize() for sentence in sentences]

    long_pauses = ' // '.join(sentences)
    return long_pauses
    

def add_yots(text: str) -> str:
    yot_table = {
        'я': 'jа',
        'ё': 'jо',
        'ю': 'jу',
        'и': 'jи',
        'е': 'jе',
    }

    result = text[0]
    for i in range(1, len(text)):
        previous, current = text[i-1], text[i]

        if previous in VOWELS and current in SOFT_VOWELS:
            result += yot_table[current.lower()]
        else:
            result += current
    return result


def to_phonetic_transcription(text: str) -> str:
    text = add_accents(text)
    text = add_softness(text)
    text = add_yots(text)
    text = add_pauses(text)

    text = ' '.join(text.split())
    return text


def main():
    texts = Path('.').absolute() / 'texts'
    output = Path('.').absolute() / 'output'
    output.mkdir(exist_ok=True)

    for filename in texts.rglob('*'):
        with open(filename, 'r', encoding='utf-8') as file:
            with open(output / filename.name, 'w', encoding='utf-8') as output_file:
                output_file.write(to_phonetic_transcription(file.read()))
    # text = text.replace('\n', ' ')
    # transcription = to_phonetic_transcription(text)

    # print(transcription)


if __name__ == "__main__":
    main()
