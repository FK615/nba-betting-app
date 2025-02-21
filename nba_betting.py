import os
import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Load API Key from Environment Variables (API-NBA)
API_NBA_KEY = os.getenv("API_NBA_KEY")  # Secure API key handling

HEADERS = {
    "x-rapidapi-host": "api-nba-v1.p.rapidapi.com",
    "x-rapidapi-key": API_NBA_KEY
}

# Fetch NBA Players from API-NBA
def get_all_nba_players():
    url = "https://api-nba-v1.p.rapidapi.com/players"
    response = requests.get(url, headers=HEADERS, timeout=5)

    if response.status_code != 200:
        return {"error": f"API request failed with status {response.status_code}"}
    
    return response.json()

# Flask Route to Fetch NBA Players
@app.route("/players", methods=["GET"])
def players():
    data = get_all_nba_players()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)


# Get Player Stats

def get_all_nba_players():
    """Fetches all active NBA players using API calls with retry logic."""
    players = []
    page = 1
    max_pages = 5  # Adjust as needed

    while page <= max_pages:
        url = f"https://api.balldontlie.io/v1/players?page={page}&per_page=100"

        try:
            response = requests.get(url, headers=BALLDONTLIE_HEADERS, timeout=3)
            response.raise_for_status()
        except RequestException as e:
            print(f"Error fetching player list (page {page}): {e}")
            break  # Stop retrying if the API is failing

        data = response.json()
        if not data.get("data"):
            break  # No more players to fetch

        players.extend(
            {"id": player["id"], "name": f"{player['first_name']} {player['last_name']}"}
            for player in data["data"]
            if player.get("team")  # Only include players with a team
        )

        page += 1

    return players


# Scrape Advanced Stats

def get_advanced_stats(player_name):
    formatted_name = "-".join(player_name.lower().split())
    url = f"https://www.basketball-reference.com/players/{formatted_name[0]}/{formatted_name[:5]}{formatted_name[6:8]}01.html"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    stats_table = soup.find('table', {'id': 'per_game'})
    if not stats_table:
        return None
    df = pd.read_html(str(stats_table))[0]
    return df.iloc[-1].to_dict()

# Get Defensive Matchups

def get_defensive_stats():
    url = "https://www.fantasypros.com/daily-fantasy/nba/fanduel-defense-vs-position.php"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return None
    df = pd.read_html(str(tables[0]))[0]
    df.columns = df.iloc[0]
    return df[1:].reset_index(drop=True)

# Generate Top 10 Over Bets

def get_best_over_bets():
    players = get_all_nba_players()
    recommendations = []
    for player in players:
        stats_df = get_nba_player_stats(player["id"])
        if stats_df.empty:
            continue
        avg_points = stats_df["pts"].mean()
        if avg_points and avg_points > 15:  # Adjusted threshold based on deeper analysis
            recommendations.append({"player": player["name"], "avg_points": avg_points})
    return sorted(recommendations, key=lambda x: x["avg_points"], reverse=True)[:10]

# Flask Routes

@app.route('/')
def index():
    return render_template("index.html", bets=get_best_over_bets())

@app.route('/api/bets')
def api_bets():
    return jsonify(get_best_over_bets())

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Use Railway’s detected port
    app.run(host="0.0.0.0", port=port, debug=True)
