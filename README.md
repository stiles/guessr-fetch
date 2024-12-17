## GeoGuessr Fetch Tools

This repository contains scripts to help you fetch and analyze data about your GeoGuessr games, including duel results, historical summaries, leaderboards and round metadata.

### Prerequisites

1. **Python 3.x** installed.
2. Required packages: `requests`, `beautifulsoup4`, `pandas`, `tqdm`, `rich`.
   - Install them using `pip install -r requirements.txt`.
3. **`config.py` File**:
   - You must create a `config.py` file in the `scripts/` directory with your **session cookies** and **headers** to access GeoGuessr API endpoints.

   Example `config.py`:
   ```python
   headers = {
       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
       "Accept-Language": "en-US,en;q=0.9",
       "Referer": "https://www.geoguessr.com/"
   }

   cookies = {
       "session": "<YOUR_SESSION_COOKIE>"
   }
   ```

   Replace `<YOUR_SESSION_COOKIE>` with your valid GeoGuessr session cookie.

---

### Scripts

#### 1. **`fetch_single_duel_summary.py`**
- **Description**: Fetch details about a single GeoGuessr duel, including your guesses, round locations and game outcome.
- **Usage**:
   - Replace the `duel_id` variable with the ID from the duel URL.
   - Run the script:
     ```bash
     python scripts/fetch_single_duel_summary.py
     ```
- **Output**:
   - Prints a list of dictionaries with details such as:
     - Actual and guessed coordinates for each round
     - User's guess distance from actual for each round
     - User's win/loss outcome

**Example JSON object:** 
```json
    {
        "duel_id": "89c51cdf-4484-4ea5-9bce-07e90003034a",
        "duel_outcome": "Win",
        "duel_opponent": "TaylorB",
        "duel_round_num": 1,
        "actual_lat": 35.70042632,
        "actual_lng": 139.8095272,
        "my_guess_lat": 35.238317611213844,
        "my_guess_lng": 136.8968754648163,
        "my_guess_distance": 268717.02495217,
        "my_guess_miles": 167.0087,
        "my_health_after": 4086
    }
```

---

#### 2. **`fetch_historical_duel_summaries.py`**
- **Description**: Fetch all your historical duels by:
   1. Scanning your browser history for duel URLs.
   2. Downloading the duel details for each duel found.
- **Requirements**:
   - Works on **Chrome** history (macOS assumed). Modify paths for other operating systems if needed.
- **Usage**:
   ```bash
   python scripts/fetch_historical_duel_summaries.py
   ```
- **Output**:
   - JSON files for each duel are saved in `data/duels/individual`.
   - A consolidated JSON file (`duel_results.json`) with round details, guesses, outcomes, and opponents.

---

#### 3. **`fetch_leaderboard.py`**
- **Description**: Fetch the GeoGuessr global leaderboard data.
- **Usage**:
   ```bash
   python scripts/fetch_leaderboard.py
   ```
- **Output**:
   - Saves leaderboard data to `data/leaderboard/geoguessr_leaders_timeseries.json` as a time series.

**Example JSON output**: 

```json
[
    {
        "position":1,
        "rating":2251,
        "userId":"5ffb5e4975d2770001545cf5",
        "nick":"apablasbe",
        "isVerified":false,
        "isDeleted":false,
        "flair":1,
        "countryCode":"gb",
        "fetched_date":"2024-12-13"
    },
    {
        "position":2,
        "rating":2242,
        "userId":"57d301d409f2efcce834fc94",
        "nick":"Radu C",
        "isVerified":true,
        "isDeleted":false,
        "flair":6,
        "countryCode":"us",
        "fetched_date":"2024-12-13"
    },
    {
        "position":3,
        "rating":2204,
        "userId":"5bf491faaac55b998458ed9a",
        "nick":"mk",
        "isVerified":true,
        "isDeleted":false,
        "flair":7,
        "countryCode":"us",
        "fetched_date":"2024-12-13"
    },
    // ~ 23,000 other users
]
```

---

#### 4. **`fetch_round_metadata.py`**
- **Description**: Fetch metadata for a specific round/location in GeoGuessr using a Google Maps API endpoint.
- **Requirements**:
   - Set your Google Maps API key in your environment:
     ```bash
     export GOOGLE_MAPS_API_KEY="YOUR_API_KEY"
     ```
- **Warning**: Do not use this during competitive play. You can and should be banned for doing so.
- **Usage**:
   - Replace the `location_id` variable with the appropriate ID.
   - Run the script:
     ```bash
     python scripts/fetch_round_metadata.py
     ```
- **Output**:
   - Prints the round location name and coordinates.

**Example**: 
```bash
Location: Zagreb, City of Zagreb
Coordinates: (45.80859592623649, 16.004239630666675)
```

---

### File Structure

```
guessr-fetch/
│
├── scripts/
│   ├── fetch_single_duel_summary.py
│   ├── fetch_historical_duel_summaries.py
│   ├── fetch_leaderboard.py
│   └── fetch_round_metadata.py
│
├── data/
│   └── duels/
│       ├── all/          # User's complete duel history as JSON
│       └── individual/   # Individual duels as JSON
│   └── leaderboard/
│
└── config.py             # Your headers and cookies
```

---

### Notes
- Use responsibly. These scripts require access to your **authenticated session**.
- Keep your `config.py` file private to avoid leaking sensitive information.
- If you accidentally commit `config.py`, remove it from the Git history.

---

### License
This project is for personal use and learning purposes only.
