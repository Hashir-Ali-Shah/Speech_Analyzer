import re
from collections import Counter
from typing import Optional
from backend.config import (
    SINGLE_FILLERS,
    MULTI_FILLERS,
    SENTENCE_START_FILLERS,
    PAUSE_THRESHOLD_SECONDS,
    MIN_PHRASE_LENGTH,
    MAX_PHRASE_LENGTH,
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def compute_core_metrics(transcript: str, duration_seconds: float) -> dict:
    words = _tokenize(transcript)
    word_count = len(words)

    wpm = round((word_count / duration_seconds) * 60, 1) if duration_seconds > 0 else 0

    sentences = _split_sentences(transcript)
    sentence_lengths = [len(_tokenize(s)) for s in sentences] if sentences else [0]

    avg_sentence_length = round(sum(sentence_lengths) / len(sentence_lengths), 1) if sentence_lengths else 0
    longest_sentence_length = max(sentence_lengths) if sentence_lengths else 0
    shortest_sentence_length = min(sentence_lengths) if sentence_lengths else 0

    return {
        "word_count": word_count,
        "words_per_minute": wpm,
        "avg_sentence_length": avg_sentence_length,
        "longest_sentence_length": longest_sentence_length,
        "shortest_sentence_length": shortest_sentence_length,
    }


def compute_filler_metrics(transcript: str, word_timestamps: Optional[list] = None) -> dict:
    text_lower = transcript.lower()
    words = _tokenize(transcript)
    word_count = len(words)
    filler_counts = Counter()
    filler_positions = []

    for i, word in enumerate(words):
        if word in SINGLE_FILLERS:
            filler_counts[word] += 1
            if word_timestamps and i < len(word_timestamps):
                filler_positions.append({
                    "filler": word,
                    "position": word_timestamps[i].get("start", 0) if isinstance(word_timestamps[i], dict) else 0,
                })

    for phrase in MULTI_FILLERS:
        phrase_lower = phrase.lower()
        start = 0
        while True:
            idx = text_lower.find(phrase_lower, start)
            if idx == -1:
                break
            filler_counts[phrase] += 1
            start = idx + len(phrase_lower)

    sentences = _split_sentences(transcript)
    for sentence in sentences:
        sentence_words = _tokenize(sentence)
        if sentence_words:
            first_word = sentence_words[0]
            if first_word in SENTENCE_START_FILLERS:
                filler_counts[first_word + " (start)"] += 1

    total_fillers = sum(filler_counts.values())
    filler_density = round((total_fillers / word_count) * 100, 1) if word_count > 0 else 0
    most_common = filler_counts.most_common(1)[0][0] if filler_counts else "none"

    return {
        "filler_count": total_fillers,
        "filler_density": filler_density,
        "most_common_filler": most_common,
        "filler_details": dict(filler_counts),
        "filler_timeline": filler_positions,
    }


def compute_repetition_metrics(transcript: str) -> dict:
    words = _tokenize(transcript)
    repeated_words = []
    repeated_phrases = []

    i = 0
    while i < len(words) - 1:
        if words[i] == words[i + 1]:
            repeated_word = words[i]
            count = 1
            while i < len(words) - 1 and words[i] == words[i + 1]:
                count += 1
                i += 1
            repeated_words.append({"word": repeated_word, "count": count})
        i += 1

    phrase_counter = Counter()
    for length in range(MIN_PHRASE_LENGTH, MAX_PHRASE_LENGTH + 1):
        for i in range(len(words) - length + 1):
            phrase = " ".join(words[i:i + length])
            phrase_counter[phrase] += 1

    common_phrases = {"i think", "it is", "in the", "of the", "to the", "and the", "on the", "is a", "for the"}
    for phrase, count in phrase_counter.items():
        if count >= 2 and phrase not in common_phrases:
            repeated_phrases.append({"phrase": phrase, "count": count})

    repeated_phrases.sort(key=lambda x: x["count"], reverse=True)
    repeated_phrases = repeated_phrases[:10]

    total_repetitions = len(repeated_words) + len(repeated_phrases)

    return {
        "repetition_count": total_repetitions,
        "repeated_words": repeated_words,
        "repeated_phrases": repeated_phrases,
    }


def compute_pause_metrics(word_timestamps: Optional[list] = None) -> dict:
    if not word_timestamps or len(word_timestamps) < 2:
        return {
            "longest_pause_seconds": 0,
            "avg_pause_duration": 0,
            "pause_count_over_1s": 0,
            "pauses": [],
        }

    pauses = []
    for i in range(1, len(word_timestamps)):
        prev_end = word_timestamps[i - 1].get("end", 0)
        curr_start = word_timestamps[i].get("start", 0)
        gap = round(curr_start - prev_end, 3)
        if gap > 0.1:
            pauses.append({
                "duration": gap,
                "after_word": word_timestamps[i - 1].get("word", ""),
                "before_word": word_timestamps[i].get("word", ""),
                "position": round(prev_end, 3),
            })

    significant_pauses = [p for p in pauses if p["duration"] >= PAUSE_THRESHOLD_SECONDS]
    all_durations = [p["duration"] for p in pauses]

    longest = round(max(all_durations), 2) if all_durations else 0
    avg_duration = round(sum(all_durations) / len(all_durations), 2) if all_durations else 0

    return {
        "longest_pause_seconds": longest,
        "avg_pause_duration": avg_duration,
        "pause_count_over_1s": len(significant_pauses),
        "pauses": significant_pauses,
    }


def compute_vocabulary_metrics(transcript: str) -> dict:
    words = _tokenize(transcript)
    word_count = len(words)

    if word_count == 0:
        return {
            "vocabulary_diversity": 0,
            "avg_word_length": 0,
            "sentence_count": 0,
            "unique_word_count": 0,
        }

    unique_words = set(words)
    unique_count = len(unique_words)
    diversity = round(unique_count / word_count, 2)

    avg_length = round(sum(len(w) for w in words) / word_count, 1)

    sentences = _split_sentences(transcript)
    sentence_count = len(sentences)

    return {
        "vocabulary_diversity": diversity,
        "avg_word_length": avg_length,
        "sentence_count": sentence_count,
        "unique_word_count": unique_count,
    }


def compute_pacing_metrics(
    duration_seconds: float,
    word_count: int,
    word_timestamps: list | None = None,
) -> dict:
    if not word_timestamps or len(word_timestamps) < 2 or duration_seconds <= 0:
        return {
            "articulation_rate": 0,
            "speaking_time_ratio": 0,
        }

    total_pause_time = 0.0
    for i in range(1, len(word_timestamps)):
        prev_end = word_timestamps[i - 1].get("end", 0)
        curr_start = word_timestamps[i].get("start", 0)
        gap = curr_start - prev_end
        if gap > 0.25:
            total_pause_time += gap

    speaking_time = max(0.01, duration_seconds - total_pause_time)
    speaking_ratio = round((speaking_time / duration_seconds) * 100, 1)
    articulation_rate = round((word_count / speaking_time) * 60, 1) if speaking_time > 0 else 0

    return {
        "articulation_rate": articulation_rate,
        "speaking_time_ratio": speaking_ratio,
    }


def compute_all_metrics(transcript: str, duration_seconds: float, word_timestamps: list | None = None) -> dict:
    core = compute_core_metrics(transcript, duration_seconds)
    fillers = compute_filler_metrics(transcript, word_timestamps)
    repetitions = compute_repetition_metrics(transcript)
    pauses = compute_pause_metrics(word_timestamps)
    vocabulary = compute_vocabulary_metrics(transcript)
    pacing = compute_pacing_metrics(duration_seconds, core["word_count"], word_timestamps)

    return {
        **core,
        **fillers,
        **repetitions,
        **pauses,
        **vocabulary,
        **pacing,
    }
