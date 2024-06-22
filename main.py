import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize

stop_words = set()
for filename in os.listdir('StopWords'):
    with open(os.path.join('StopWords', filename), 'r') as file:
        stop_words.update(file.read().split())

positive_words = set()
negative_words = set()
with open('MasterDictionary/positive-words.txt', 'r') as file:
    positive_words.update(file.read().split())
with open('MasterDictionary/negative-words.txt', 'r') as file:
    negative_words.update(file.read().split())

positive_words -= stop_words
negative_words -= stop_words
def extract_article_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extracting article title and text
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
        paragraphs = soup.find_all('p')
        text = ' '.join([para.get_text(strip=True) for para in paragraphs])

        return title + '\n' + text
    except Exception as e:
        print(f"Failed to extract {url}: {e}")
        return ""


def clean_text(text):
    tokens = word_tokenize(text.lower())
    cleaned_tokens = [token for token in tokens if token.isalnum() and token not in stop_words]
    return cleaned_tokens
def count_syllables(word):
    word = word.lower()
    vowels = 'aeiou'
    syllable_count = 0
    if word[0] in vowels:
        syllable_count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            syllable_count += 1
    if word.endswith(('es', 'ed')):
        syllable_count -= 1
    if syllable_count == 0:
        syllable_count += 1
    return syllable_count


def calculate_metrics(text):
    sentences = sent_tokenize(text)
    words = clean_text(text)
    word_count = len(words)

    positive_score = sum(1 for word in words if word in positive_words)
    negative_score = sum(1 for word in words if word in negative_words)
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (word_count + 0.000001)

    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    complex_words = [word for word in words if count_syllables(word) > 2]
    complex_word_count = len(complex_words)
    percentage_complex_words = complex_word_count / word_count if word_count > 0 else 0

    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)

    syllable_count = sum(count_syllables(word) for word in words)
    syllables_per_word = syllable_count / word_count if word_count > 0 else 0

    personal_pronouns = len(re.findall(r'\b(I|we|my|ours|us)\b', text, re.I))

    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0

    metrics = {
        'Positive Score': positive_score,
        'Negative Score': negative_score,
        'Polarity Score': polarity_score,
        'Subjectivity Score': subjectivity_score,
        'Avg Sentence Length': avg_sentence_length,
        'Percentage of Complex Words': percentage_complex_words,
        'Fog Index': fog_index,
        'Avg Number of Words Per Sentence': avg_sentence_length,
        'Complex Word Count': complex_word_count,
        'Word Count': word_count,
        'Syllable per Word': syllables_per_word,
        'Personal Pronouns': personal_pronouns,
        'Avg Word Length': avg_word_length,
    }

    return metrics

input_df = pd.read_excel('Input.xlsx')

os.makedirs('articles', exist_ok=True)

results = []
for index, row in input_df.iterrows():
    url_id = row['URL_ID']
    url = row['URL']
    article_text = extract_article_text(url)

    if article_text:
        with open(f'articles/{url_id}.txt', 'w', encoding='utf-8') as file:
            file.write(article_text)

        metrics = calculate_metrics(article_text)
        result = {
            'URL_ID': url_id,
            'URL': row['URL'],
        }
        result.update(metrics)
        results.append(result)
    else:
        print(f"No content for URL ID: {url_id}")

output_df = pd.DataFrame(results)
output_df.to_csv('Output.csv', index=False)
