import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# 1. Load your labeled structured logs
df = pd.read_csv('logs/structured_logs.csv')

# 2. Filter only rows that have labels (ignore unlabeled ones)
df = df[df['incident_type'].notnull()]

# 3. Separate features and labels
X = df['message']                   # input: log message text
y = df['incident_type']            # output: incident type (label)

# 4. Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 5. Convert text into numerical features using TF-IDF
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# 6. Train the classifier
model = LogisticRegression()
model.fit(X_train_tfidf, y_train)

# 7. Make predictions on test set
y_pred = model.predict(X_test_tfidf)

# 8. Print performance metrics
print("\n📊 Model Evaluation:\n")
print(classification_report(y_test, y_pred))