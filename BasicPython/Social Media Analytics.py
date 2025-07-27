
from collections import Counter, defaultdict

users = {
    "alice": {"followers": 120, "following": 80},
    "bob": {"followers": 200, "following": 150},
    "charlie": {"followers": 90, "following": 60}
}

posts = [
    {"user": "alice", "likes": 45, "tags": ["python", "coding", "fun"]},
    {"user": "bob", "likes": 100, "tags": ["python", "tutorial"]},
    {"user": "alice", "likes": 30, "tags": ["fun", "life"]},
    {"user": "charlie", "likes": 60, "tags": ["coding", "python"]},
    {"user": "bob", "likes": 80, "tags": ["life", "fun"]},
    {"user": "alice", "likes": 55, "tags": ["python", "fun"]},
]

all_tags = [tag for post in posts for tag in post["tags"]]
tag_counter = Counter(all_tags)
most_common_tags = tag_counter.most_common()
print("1. Most Popular Tags:")
for tag, count in most_common_tags:
    print(f"{tag}: {count}")

user_likes = defaultdict(int)
for post in posts:
    user_likes[post["user"]] += post["likes"]
print("\n2. Total Likes Per User:")
for user, likes in user_likes.items():
    print(f"{user}: {likes}")

top_posts = sorted(posts, key=lambda x: x["likes"], reverse=True)
print("\n3. Top Posts by Likes:")
for post in top_posts:
    print(f"User: {post['user']}, Likes: {post['likes']}, Tags: {post['tags']}")

user_summary = {}
for user in users:
    summary = {
        "posts_count": 0,
        "total_likes": 0,
        "followers": users[user]["followers"],
        "following": users[user]["following"]
    }
    for post in posts:
        if post["user"] == user:
            summary["posts_count"] += 1
            summary["total_likes"] += post["likes"]
    user_summary[user] = summary

print("\n4. User Activity Summary:")
for user, summary in user_summary.items():
    print(f"{user}: {summary}")
