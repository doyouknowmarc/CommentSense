from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

def count_tokens(text):
    # Load the tokenizer for DistilBERT SST-2
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    
    # Tokenize the input text
    tokens = tokenizer.tokenize(text)
    
    # Print tokenized output
    print("Tokens:", tokens)
    print("Token count:", len(tokens))
    
    return len(tokens)

def classify_text(text):
    # Load the tokenizer and model for DistilBERT SST-2
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    
    # Tokenize the input text for the model (includes padding, truncation, etc.)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    
    # Get model prediction
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # SST-2 is a binary classification (negative=0, positive=1)
    negative_score = predictions[0][0].item()
    positive_score = predictions[0][1].item()
    
    print(f"Classification results:")
    print(f"Negative sentiment: {negative_score:.4f} ({negative_score*100:.2f}%)")
    print(f"Positive sentiment: {positive_score:.4f} ({positive_score*100:.2f}%)")
    
    sentiment = "positive" if positive_score > negative_score else "negative"
    print(f"Overall sentiment: {sentiment}")
    
    return sentiment, {"negative": negative_score, "positive": positive_score}

if __name__ == "__main__":
    #text = input("Enter text to tokenize: ")
    text= """
I really enjoy this channel. Your card manipulation skills are mind blowing. Take care eh
    all right this one got my attention for
$500 the request the request how about
you learn how toing talk you all right
this one got my attention for $500 this
request is for Dr Elana a
top cosmetic
dentist in San Diego feels like I'm
advertising pull a queen and an ace
together from the
waterfall oh that's easy and then uh
have the King of Hearts Leap out of the
deck well we're going to have to fire up
the old CGI machines over there you guys
hear that King from the deck um pulling
a queen and an ace together that's
pretty
easy uh apparently doing running cuts to
the table is difficult because we just
drop some cards that's all right
then um let's make it
happen Ace and a queen together Shuff is
legit
obviously uh nothing on top nothing on
the bottom no Ace Queen nothing in my
hands um yeah you good Ace and queen let
me just touch my face and palm of Ace
and queen all right that's
easy now this next
bit uh getting a king of hearts the one
and only King of Hearts to LEAP out of
the deck it's going to be difficult
because generally cards don't leap out
of a deck but we'll try this I
can't I wasn't really paying attention
to how many times these cards were
shuffled but we'll try something before
we continue only two
cards I will push these cards into the
deck like
this and I will push down like this and
one card will
leap from the top of the deck and that
is in
fact the king of
I am so good anyway that's 500
bucks
$500 and uh if you're in San Diego and
you want a top cosmetic dentist there's
only one place to
go it's that easy
folks it's that that easy welcome to the
hustle
"""
    count_tokens(text)
    classify_text(text)
