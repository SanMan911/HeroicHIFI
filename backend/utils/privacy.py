import re

NUMBER_WORDS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "trillion",
    "lakh", "lakhs", "crore", "crores",
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
    "\u0936\u0942\u0928\u094d\u092f", "\u090f\u0915", "\u0926\u094b", "\u0924\u0940\u0928", "\u091a\u093e\u0930", "\u092a\u093e\u0901\u091a", "\u091b\u0939", "\u0938\u093e\u0924", "\u0906\u0920", "\u0928\u094c", "\u0926\u0938",
    "\u0917\u094d\u092f\u093e\u0930\u0939", "\u092c\u093e\u0930\u0939", "\u0924\u0947\u0930\u0939", "\u091a\u094c\u0926\u0939", "\u092a\u0902\u0926\u094d\u0930\u0939", "\u0938\u094b\u0932\u0939", "\u0938\u0924\u094d\u0930\u0939", "\u0905\u0920\u093e\u0930\u0939", "\u0909\u0928\u094d\u0928\u0940\u0938",
    "\u092c\u0940\u0938", "\u0924\u0940\u0938", "\u091a\u093e\u0932\u0940\u0938", "\u092a\u091a\u093e\u0938", "\u0938\u093e\u0920", "\u0938\u0924\u094d\u0924\u0930", "\u0905\u0920\u094d\u0920\u093e\u0930\u0939", "\u0928\u092c\u094d\u092c\u0947",
    "\u0938\u094c", "\u0939\u091c\u093c\u093e\u0930", "\u0932\u093e\u0916", "\u0915\u0930\u094b\u0921\u093c",
]


def strip_numbers(text: str) -> str:
    if not text:
        return text
    result = re.sub(r'\d+', '[*]', text)
    for word in NUMBER_WORDS:
        escaped = re.escape(word)
        if word.isascii():
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(escaped, re.IGNORECASE)
        result = pattern.sub('[*]', result)
    return result
