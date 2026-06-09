"""
Beginner Weather App with Error Handling

This version uses real weather data from Open-Meteo.

Important idea:
1. A city name is not enough for most weather APIs.
2. We first convert the city name into latitude and longitude.
3. Then we ask the weather API for current weather at that location.
4. We handle possible errors instead of letting the program crash.
"""

import json
import tkinter as tk
from tkinter import messagebox
import urllib.error
import urllib.parse
import urllib.request


GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_json(url, params):
    """
    Send a request to an API and return the JSON response as a Python dictionary.

    url:
        The API address.

    params:
        Extra values sent to the API, such as city name or latitude.

    Why this function exists:
        Both our geocoding API and weather API need the same request logic,
        so we write it once and reuse it.
    """
    query_string = urllib.parse.urlencode(params)
    full_url = url + "?" + query_string

    try:
        with urllib.request.urlopen(full_url, timeout=10) as response:
            if response.status != 200:
                raise RuntimeError("The API returned status code " + str(response.status))

            response_text = response.read().decode("utf-8")
            return json.loads(response_text)

    except urllib.error.HTTPError as error:
        raise RuntimeError("API error: " + str(error.code)) from error

    except urllib.error.URLError as error:
        raise RuntimeError("Network error. Please check your internet connection.") from error

    except TimeoutError as error:
        raise RuntimeError("Network timeout. The weather service took too long.") from error

    except json.JSONDecodeError as error:
        raise RuntimeError("API error. The weather service returned invalid data.") from error


def get_location(city):
    """
    Convert a city name into location details.

    If the city name is invalid, the geocoding API returns no results.
    That is how we detect an invalid city.
    """
    data = get_json(
        GEOCODING_API_URL,
        {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
    )

    results = data.get("results", [])

    if len(results) == 0:
        raise ValueError("Invalid city name. Please enter a real city.")

    return results[0]


def get_weather(location):
    """
    Get current weather data for a location.

    The location must contain latitude and longitude.
    """
    data = get_json(
        WEATHER_API_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,precipitation,cloud_cover,uv_index",
            "timezone": "auto",
        },
    )

    current = data.get("current")

    if current is None:
        raise RuntimeError("API error. Current weather data is missing.")

    return current


def get_air_quality(location):
    """
    Get current air quality data for a location.

    Air quality comes from a different Open-Meteo API endpoint.
    """
    data = get_json(
        AIR_QUALITY_API_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone",
            "timezone": "auto",
        },
    )

    current = data.get("current")

    if current is None:
        raise RuntimeError("API error. Current air quality data is missing.")

    return current


def format_weather_report(location, weather):
    """
    Create the weather report text.

    In the command-line version, we used print().
    In the GUI version, we return text so Tkinter can display it on the screen.
    """
    weather_code = weather.get("weather_code")
    condition = WEATHER_CODES.get(weather_code, "Unknown condition")

    city = location.get("name", "Unknown city")
    country = location.get("country", "Unknown country")

    return (
        "Weather Report\n"
        "--------------\n"
        f"City: {city}, {country}\n"
        f"Temperature: {weather.get('temperature_2m')} C\n"
        f"Weather Condition: {condition}\n"
        f"Humidity: {weather.get('relative_humidity_2m')} %\n"
        f"Wind Speed: {weather.get('wind_speed_10m')} km/h\n"
        f"Pressure: {weather.get('pressure_msl')} hPa"
    )


class WeatherApp:
    """
    This class creates and controls the Tkinter window.

    A class is useful here because the GUI has several related parts:
    the window, city input box, search button, and weather display area.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App")
        self.root.geometry("560x620")
        self.root.resizable(False, False)
        self.root.config(bg="#eaf4fb")

        self.main_frame = tk.Frame(root, bg="#eaf4fb")
        self.main_frame.pack(fill="both", expand=True, padx=24, pady=22)

        self.title_label = tk.Label(
            self.main_frame,
            text="Weather App",
            font=("Arial", 24, "bold"),
            bg="#eaf4fb",
            fg="#18324a",
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            self.main_frame,
            text="Search current weather by city",
            font=("Arial", 11),
            bg="#eaf4fb",
            fg="#5f7485",
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 18))

        self.search_frame = tk.Frame(self.main_frame, bg="#eaf4fb")
        self.search_frame.pack(fill="x")

        self.city_entry = tk.Entry(
            self.search_frame,
            width=30,
            font=("Arial", 13),
            bd=0,
            relief="flat",
            bg="white",
            fg="#18324a",
            insertbackground="#18324a",
        )
        self.city_entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 10))
        self.city_entry.focus()
        self.city_entry.bind("<Return>", self.search_weather)

        self.search_button = tk.Button(
            self.search_frame,
            text="Search",
            font=("Arial", 12, "bold"),
            bg="#2374ab",
            fg="white",
            activebackground="#195b87",
            activeforeground="white",
            bd=0,
            cursor="hand2",
            command=self.search_weather,
        )
        self.search_button.pack(side="right", ipadx=20, ipady=10)

        self.status_label = tk.Label(
            self.main_frame,
            text="Ready",
            font=("Arial", 10),
            bg="#eaf4fb",
            fg="#5f7485",
        )
        self.status_label.pack(anchor="w", pady=(10, 14))

        self.panel_container = tk.Frame(self.main_frame, bg="white")
        self.panel_container.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(
            self.panel_container,
            bg="white",
            highlightthickness=0,
        )
        self.scrollbar = tk.Scrollbar(
            self.panel_container,
            orient="vertical",
            command=self.scroll_canvas.yview,
        )
        self.scroll_canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.weather_panel = tk.Frame(self.scroll_canvas, bg="white")
        self.weather_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.weather_panel,
            anchor="nw",
        )

        self.weather_panel.bind("<Configure>", self.update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self.resize_scroll_window)
        self.scroll_canvas.bind_all("<MouseWheel>", self.scroll_with_mouse)

        self.empty_label = tk.Label(
            self.weather_panel,
            text="Enter a city name and click Search.",
            font=("Arial", 14),
            bg="white",
            fg="#5f7485",
        )
        self.empty_label.pack(expand=True)

    def update_scroll_region(self, event=None):
        """
        Tell the canvas how tall the inside content is.

        Without this, the scrollbar does not know there is more content below.
        """
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def resize_scroll_window(self, event):
        """
        Keep the scrollable frame the same width as the canvas.
        """
        self.scroll_canvas.itemconfig(self.weather_window, width=event.width)

    def scroll_with_mouse(self, event):
        """
        Allow mouse wheel scrolling inside the weather display area.
        """
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear_weather_panel(self):
        """
        Remove old weather information before showing new information.
        """
        for widget in self.weather_panel.winfo_children():
            widget.destroy()

    def draw_icon(self, parent, icon_name):
        """
        Draw a small icon using Tkinter Canvas.

        Canvas lets us draw shapes like circles, lines, and arcs.
        This avoids needing image files or extra icon packages.
        """
        canvas = tk.Canvas(parent, width=42, height=42, bg="white", highlightthickness=0)

        if icon_name == "temperature":
            canvas.create_oval(15, 25, 27, 37, fill="#f2645a", outline="#f2645a")
            canvas.create_rectangle(18, 8, 24, 30, fill="#f2645a", outline="#f2645a")
            canvas.create_oval(17, 5, 25, 13, fill="white", outline="#f2645a", width=2)
        elif icon_name == "condition":
            canvas.create_oval(9, 9, 29, 29, fill="#f7c948", outline="#f7c948")
            canvas.create_line(32, 32, 38, 38, fill="#f7c948", width=3)
            canvas.create_line(4, 4, 10, 10, fill="#f7c948", width=3)
        elif icon_name == "humidity":
            canvas.create_polygon(21, 5, 9, 24, 21, 39, 33, 24, fill="#2f9ed8", outline="#2f9ed8")
            canvas.create_oval(16, 25, 26, 35, fill="#8fd3f4", outline="#8fd3f4")
        elif icon_name == "wind":
            canvas.create_line(6, 14, 31, 14, fill="#5f7485", width=3, capstyle="round")
            canvas.create_line(6, 23, 36, 23, fill="#5f7485", width=3, capstyle="round")
            canvas.create_line(6, 32, 26, 32, fill="#5f7485", width=3, capstyle="round")
            canvas.create_arc(27, 8, 39, 20, start=270, extent=180, outline="#5f7485", width=3)
        elif icon_name == "pressure":
            canvas.create_arc(8, 10, 34, 36, start=0, extent=180, outline="#8b5cf6", width=3)
            canvas.create_line(21, 23, 30, 15, fill="#8b5cf6", width=3, capstyle="round")
            canvas.create_oval(18, 20, 24, 26, fill="#8b5cf6", outline="#8b5cf6")
        elif icon_name == "rain":
            canvas.create_oval(9, 10, 33, 24, fill="#d8e7f1", outline="#8aa6b8")
            canvas.create_line(13, 29, 10, 36, fill="#2f9ed8", width=2)
            canvas.create_line(22, 29, 19, 36, fill="#2f9ed8", width=2)
            canvas.create_line(31, 29, 28, 36, fill="#2f9ed8", width=2)
        elif icon_name == "cloud":
            canvas.create_oval(8, 17, 22, 31, fill="#b9cad6", outline="#b9cad6")
            canvas.create_oval(17, 10, 32, 31, fill="#b9cad6", outline="#b9cad6")
            canvas.create_rectangle(10, 22, 35, 32, fill="#b9cad6", outline="#b9cad6")
        elif icon_name == "uv":
            canvas.create_oval(12, 12, 30, 30, fill="#f59e0b", outline="#f59e0b")
            canvas.create_text(21, 21, text="UV", fill="white", font=("Arial", 9, "bold"))
        elif icon_name == "air":
            canvas.create_line(6, 13, 35, 13, fill="#10b981", width=3, capstyle="round")
            canvas.create_line(12, 22, 36, 22, fill="#10b981", width=3, capstyle="round")
            canvas.create_line(6, 31, 29, 31, fill="#10b981", width=3, capstyle="round")

        return canvas

    def create_metric_card(self, parent, row, column, icon_name, title, value):
        """
        Create one small weather card.

        Each card contains an icon, a label, and the value.
        """
        card = tk.Frame(parent, bg="white", highlightbackground="#d8e7f1", highlightthickness=1)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)

        icon = self.draw_icon(card, icon_name)
        icon.pack(anchor="w", padx=14, pady=(14, 4))

        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 10),
            bg="white",
            fg="#5f7485",
        )
        title_label.pack(anchor="w", padx=14)

        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#18324a",
            wraplength=190,
            justify="left",
        )
        value_label.pack(anchor="w", padx=14, pady=(2, 14))

    def show_weather_result(self, location, weather, air_quality, air_quality_error):
        """
        Display the weather information in the window.
        """
        self.clear_weather_panel()

        weather_code = weather.get("weather_code")
        condition = WEATHER_CODES.get(weather_code, "Unknown condition")
        city = location.get("name", "Unknown city")
        country = location.get("country", "Unknown country")

        header = tk.Frame(self.weather_panel, bg="white")
        header.pack(fill="x", padx=22, pady=(22, 12))

        location_label = tk.Label(
            header,
            text=f"{city}, {country}",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="#18324a",
        )
        location_label.pack(anchor="w")

        condition_label = tk.Label(
            header,
            text=condition,
            font=("Arial", 12),
            bg="white",
            fg="#5f7485",
        )
        condition_label.pack(anchor="w", pady=(2, 0))

        temperature_label = tk.Label(
            header,
            text=f"{weather.get('temperature_2m')} C",
            font=("Arial", 42, "bold"),
            bg="white",
            fg="#2374ab",
        )
        temperature_label.pack(anchor="w", pady=(8, 0))

        cards_frame = tk.Frame(self.weather_panel, bg="white")
        cards_frame.pack(fill="both", expand=True, padx=14, pady=(4, 18))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        self.create_metric_card(cards_frame, 0, 0, "temperature", "Temperature", f"{weather.get('temperature_2m')} C")
        self.create_metric_card(cards_frame, 0, 1, "temperature", "Feels Like", f"{weather.get('apparent_temperature')} C")
        self.create_metric_card(cards_frame, 1, 0, "condition", "Condition", condition)
        self.create_metric_card(cards_frame, 1, 1, "humidity", "Humidity", f"{weather.get('relative_humidity_2m')} %")
        self.create_metric_card(cards_frame, 2, 0, "wind", "Wind Speed", f"{weather.get('wind_speed_10m')} km/h")
        self.create_metric_card(cards_frame, 2, 1, "pressure", "Pressure", f"{weather.get('pressure_msl')} hPa")
        self.create_metric_card(cards_frame, 3, 0, "rain", "Precipitation", f"{weather.get('precipitation')} mm")
        self.create_metric_card(cards_frame, 3, 1, "cloud", "Cloud Cover", f"{weather.get('cloud_cover')} %")
        self.create_metric_card(cards_frame, 4, 0, "uv", "UV Index", str(weather.get("uv_index")))

        if air_quality_error:
            self.create_metric_card(cards_frame, 4, 1, "air", "Air Quality", "Not available")
        else:
            self.create_metric_card(cards_frame, 4, 1, "air", "US AQI", str(air_quality.get("us_aqi")))
            self.create_metric_card(cards_frame, 5, 0, "air", "PM10", f"{air_quality.get('pm10')} ug/m3")
            self.create_metric_card(cards_frame, 5, 1, "air", "PM2.5", f"{air_quality.get('pm2_5')} ug/m3")
            self.create_metric_card(cards_frame, 6, 0, "air", "Nitrogen Dioxide", f"{air_quality.get('nitrogen_dioxide')} ug/m3")
            self.create_metric_card(cards_frame, 6, 1, "air", "Ozone", f"{air_quality.get('ozone')} ug/m3")

        self.update_scroll_region()

    def search_weather(self, event=None):
        """
        Run when the user clicks Search or presses Enter.

        event=None is used because button clicks do not send an event,
        but pressing Enter does.
        """
        city_name = self.city_entry.get().strip()

        if city_name == "":
            messagebox.showwarning("Missing City", "Please enter a city name.")
            return

        self.search_button.config(state="disabled", text="Searching...")
        self.status_label.config(text="Searching weather data...")
        self.root.update_idletasks()

        try:
            location = get_location(city_name)
            weather = get_weather(location)
            air_quality = {}
            air_quality_error = None

            try:
                air_quality = get_air_quality(location)
            except RuntimeError as error:
                air_quality_error = str(error)

            self.show_weather_result(location, weather, air_quality, air_quality_error)
            self.status_label.config(text="Weather updated successfully")

        except ValueError as error:
            self.status_label.config(text="City not found")
            messagebox.showerror("City Error", str(error))

        except RuntimeError as error:
            self.status_label.config(text="Could not load weather")
            messagebox.showerror("Weather App Error", str(error))

        except KeyError:
            self.status_label.config(text="Weather data was incomplete")
            messagebox.showerror(
                "API Error",
                "Some expected weather data was missing.",
            )

        finally:
            self.search_button.config(state="normal", text="Search")


def main():
    """
    Create the main Tkinter window and start the GUI event loop.

    mainloop() keeps the window open and waits for user actions,
    such as button clicks and keyboard presses.
    """
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
