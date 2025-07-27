from collections import Counter
import re

class TextAnalyzer:
    def __init__(self, text):
        self.text = text
        self.text_lower = text.lower()

    def get_character_frequency(self, include_spaces=False):
        """
        Returns a Counter of character frequencies.
        If include_spaces is False, spaces are excluded.
        """
        if include_spaces:
            chars = self.text
        else:
            chars = self.text.replace(" ", "")
        return Counter(chars)

    def get_word_frequency(self, min_length=1):
        """
        Returns a Counter of word frequencies, filtering out words shorter than min_length.
        """
        words = re.findall(r'\b\w+\b', self.text_lower)
        filtered_words = [w for w in words if len(w) >= min_length]
        return Counter(filtered_words)

    def get_sentence_length_distribution(self):
        """
        Returns a dictionary with statistics about sentence lengths (in words).
        """
        sentences = re.split(r'[.!?]+', self.text)
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences if s.strip()]
        if not sentence_lengths:
            return {
                "min": 0,
                "max": 0,
                "average": 0,
                "distribution": {}
            }
        distribution = Counter(sentence_lengths)
        return {
            "min": min(sentence_lengths),
            "max": max(sentence_lengths),
            "average": sum(sentence_lengths) / len(sentence_lengths),
            "distribution": dict(distribution)
        }

    def find_common_words(self, n=10, exclude_common=True):
        """
        Returns the n most common words, optionally excluding common English stopwords.
        """
        common_words = set([
            "the", "and", "is", "in", "it", "of", "to", "a", "for", "on", "with", "as", "by", "an", "at", "be", "this",
            "that", "from", "or", "are", "was", "but", "not", "have", "has", "had", "they", "you", "he", "she", "we",
            "his", "her", "their", "our", "were", "which", "will", "would", "can", "could", "should", "do", "does",
            "did", "so", "if", "about", "into", "than", "then", "them", "these", "those", "its", "also"
        ])
        word_freq = self.get_word_frequency(min_length=1)
        if exclude_common:
            for word in common_words:
                word_freq.pop(word, None)
        return word_freq.most_common(n)

    def get_reading_statistics(self):
        """
        Returns a dictionary with character count, word count, sentence count,
        average word length, and estimated reading time (words/200 per min).
        """
        char_count = len(self.text)
        words = re.findall(r'\b\w+\b', self.text)
        word_count = len(words)
        sentences = re.split(r'[.!?]+', self.text)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_word_length = sum(len(w) for w in words) / word_count if word_count else 0
        reading_time_min = word_count / 200 if word_count else 0
        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "average_word_length": avg_word_length,
            "estimated_reading_time_min": reading_time_min
        }

    def compare_with_text(self, other_text):
        """
        Compares the current text with another text and returns similarity metrics.
        """
        other_words = re.findall(r'\b\w+\b', other_text.lower())
        self_words = re.findall(r'\b\w+\b', self.text_lower)
        set_self = set(self_words)
        set_other = set(other_words)
        common = set_self & set_other
        union = set_self | set_other
        jaccard = len(common) / len(union) if union else 0
        return {
            "common_word_count": len(common),
            "total_unique_words": len(union),
            "jaccard_similarity": jaccard
        }

if __name__ == "__main__":
    sample_text = (
        "Python is a powerful programming language. "
        "It is widely used for web development, data analysis, artificial intelligence, and more. "
        "Python's syntax is clear and easy to learn. "
        "Many developers love Python for its versatility and community support."
    )
    analyzer = TextAnalyzer(sample_text)

    print("Character frequency (no spaces):", analyzer.get_character_frequency())
    print("Word frequency (min length 3):", analyzer.get_word_frequency(min_length=3))
    print("Sentence length distribution:", analyzer.get_sentence_length_distribution())
    print("Most common words (excluding stopwords):", analyzer.find_common_words(n=5))
    print("Reading statistics:", analyzer.get_reading_statistics())

    other_text = (
        "Java is another popular programming language. "
        "It is used for building enterprise applications and Android apps."
    )
    print("Comparison with another text:", analyzer.compare_with_text(other_text))
