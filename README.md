# FC26 API

This repository contains a Python script (`fc26_api.py`) that allows you to retrieve data from the EA Sports FC 24 Pro Clubs API. With this script, you can get detailed information about any club and search for clubs by their names.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.x
* pandas
* requests

### Installing

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/fc26-api.git
   ```
2. Install the required libraries:
   ```bash
   pip install pandas requests
   ```

## Usage

The `fc26_api.py` script provides two main functions:

* `get_club_details(club_id)`: Retrieves detailed information about a specific club.
* `search_club_by_name(club_name)`: Searches for a club by its name and returns a list of matching clubs.

### Example

To use the functions, you can import them into your own Python script:

```python
from fc26_api import get_club_details, search_club_by_name

# Get club details by ID
club_id = "12345"
club_details = get_club_details(club_id)
print(club_details)

# Search for a club by name
club_name = "Your Club Name"
clubs = search_club_by_name(club_name)
print(clubs)
```

## Built With

* [Python](https://www.python.org/) - The programming language used
* [pandas](https://pandas.pydata.org/) - For data manipulation and analysis
* [requests](https://requests.readthedocs.io/en/latest/) - For making HTTP requests

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have any suggestions or find any bugs.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
