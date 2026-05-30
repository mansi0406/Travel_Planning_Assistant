# Agentic AI Travel Planning Assistant

## 📌 Project Overview
Planning a trip often involves comparing flights, hotels, attractions, weather, and budgets across multiple platforms, which is time-consuming and inefficient.  
The **Agentic AI Travel Planning Assistant** is an intelligent, agent-based system that autonomously generates optimized travel itineraries using structured datasets and live weather data, while reasoning like a human travel expert.

This project demonstrates **Agentic AI using LangChain**, JSON-based tools, and a **Streamlit UI** to deliver clean, explainable, and user-friendly trip plans.

---

## 🎯 Problem Statement
Travelers often struggle with:
- Comparing inconsistent flight and hotel information  
- Manually building itineraries  
- Estimating realistic budgets  
- Understanding weather impacts on travel plans  

There is a need for an **automated, intelligent travel assistant** that can:
- Reason step-by-step
- Use multiple data sources
- Generate complete, structured itineraries

---

## 💼 Business Use Cases
AI-driven travel agents can help:
- Reduce customer support workload
- Provide personalized recommendations
- Automate itinerary creation
- Improve customer satisfaction
- Save time and money for travelers

Applicable to platforms like travel agencies, airline aggregators, hotel booking platforms, and tourism portals.

---

## ✅ Project Objectives

### Primary Objectives
1. Build an **agentic AI system** using LangChain.
2. Integrate tools for:
   - Flight search (JSON dataset)
   - Hotel recommendations (JSON dataset)
   - Places / POIs discovery (JSON dataset)
   - Real-time weather lookup (Open-Meteo API)
3. Enable **multi-step reasoning** using ReAct / ToolCalling agents.
4. Generate **structured itineraries** including:
   - Trip summary
   - Day-wise plan
   - Accommodation
   - Weather expectations
   - Budget estimation

### Secondary Objectives
5. Implement filtering and optimization (cheapest flight, best-rated hotel).
6. Provide decision justification (“Why this option was selected”).
7. Output results in **clean JSON + human-readable format**.
8. Provide a simple **Streamlit-based UI**.

---

## 🧠 Project Architecture (High-Level)
1. User enters trip details via Streamlit UI.
2. LangChain agent interprets the request.
3. Agent autonomously calls tools:
   - Flight Tool
   - Hotel Tool
   - Places Tool
   - Weather Tool
   - Budget Estimator
4. Results are analyzed and combined.
5. Final itinerary is generated in:
   - Human-readable format (UI)
   - Structured JSON (for validation & reuse)

---

## 📂 Project Structure
```
AgenticTravelAssistant/
│
├── src/ # Core application source code
│ ├── pycache/ # Python bytecode cache
│ ├── init.py # Marks src as a Python package
│ ├── app.py # Streamlit UI – user inputs & final output display
│ ├── agent.py # LangChain agent with multi-step reasoning (ReAct / ToolCalling)
│ ├── planner.py # Orchestrates itinerary creation logic
│ ├── tools.py # LangChain tools:
│ │ # - Flight search (flights.json)
│ │ # - Hotel recommendations (hotels.json)
│ │ # - Places / POIs discovery (places.json)
│ │ # - Weather lookup (Open-Meteo API)
│ │ # - Budget estimation
│ ├── data_access.py # JSON data loaders & dataset access helpers
│ └──  schemas.py # Pydantic / schema definitions for structured outputs
│
├── data/ # Static datasets (input data)
│ ├── flights.json # Flight dataset (source, destination, price, duration)
│ ├── hotels.json # Hotel dataset (city, rating, price per night)
│ └── places.json # Places / POIs dataset (city, type, rating)
│
├── tests/ # Automated test suite (pytest)
│ ├── pycache/ # Test bytecode cache
│ ├── conftest.py # Shared pytest fixtures & dataset loaders
│ ├── test_agent.py # Tests agent reasoning & end-to-end flow
│ ├── test_agent_plan_trip_output.py# Validates final itinerary structure & content
│ ├── test_tools.py # Tests individual tools (flight, hotel, places, weather)
│ ├── test_basic_filters_matching.py# Verifies filtering & ranking logic
│ ├── test_budget_graceful_when_blank.py
│ │ # Ensures budget estimation works with missing inputs
│ ├── test_json_files_exist_and_valid.py
│ │ # Checks JSON datasets exist & are schema-valid
│ ├── test_schema_flights_hotels_places.py
│ │ # Schema validation for input datasets
│ ├── test_structured_text_formatters_do_not_crash.py
│ │ # Ensures output formatting is robust
│ └── test.py # Optional single test runner / aggregation script
│
├── requirements.txt
└── README.md
```

---

## 🧪 Data Sources

### Static JSON Datasets
- **flights.json** – Flight details (source, destination, price, duration)
- **hotels.json** – Hotel details (city, rating, price)
- **places.json** – Attractions and POIs (city, type, rating)

### Live API
- **Weather API:** Open-Meteo  
  - Free, no API key required  
  - Provides weather forecasts for travel dates  

---

## 🛠️ Tools Implemented
- **Flight Search Tool**
  - Filters by source & destination
  - Selects cheapest / fastest option
- **Hotel Recommendation Tool**
  - Filters by city, rating, and price
- **Places Discovery Tool**
  - Recommends attractions based on type & rating
- **Weather Lookup Tool**
  - Fetches live forecast from Open-Meteo
- **Budget Estimation Tool**
  - Calculates total cost (flight + hotel + local expenses)
  - Works even if flight or hotel data is missing

---

## 🧪 Testing
- Unit tests implemented using **pytest**
- Tests cover:
  - Tool logic
  - Agent responses
  - Data loading and validation
- Test results are written to `outputs/pytest_results.txt`

## Run tests:
```bash
pytest -v --disable-warnings > outputs/test_results.txt
```

## Create and activate virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
```

## Install dependencies: 
```bash
pip install -r requirements.txt

```

## Run the Streamlit app : 
```bash
streamlit run src/app.py

```

## Open the browser by clicking on the link (if browser not automatically appearing): 
```
http://localhost:8501

```

## 📤 Output Format : 
```
### Human-Readable (UI)
- Trip Summary
- Flight selected
- Hotel recommendation
- Day-wise itinerary
- Weather forecast
- Budget breakdown
- Structured JSON
- Inputs used
- Tool outputs
- Final itinerary
- Cost estimation
```
---

## 📊 Sample Output (Example) : 

Your 6-Day Trip to Bangalore (May 29–Jun 3)

Flight:
- Air India – ₹3,695

Hotel:
- Green Leaf Resort –  ₹5,018/night (4★)

Weather:
- 2026-05-29: Thunderstorm, 35.1°C / 28.7°C
- 2026-05-30: Thunderstorm, 34.8°C / 28.7°C
- 2026-05-31: Thunderstorm, 33.6°C / 28.9°C
- 2026-06-01: Thunderstorm, 33.6°C / 28.7°C
- 2026-06-02: Thunderstorm, 32.9°C / 28.7°C
- 2026-06-03: Thunderstorm, 32.8°C / 28.9°C

Itinerary:
- Day 1: Historic Fort (temple), Popular Fort (park), Historic Fort (market) 
- Day 2: Scenic Museum (market), Shopping at a local market / mall, Street food + shopping street
- Day 3: Temple visit, art gallery, Cultural show / live music
- Day 4: Guided food trail / cafe hopping, Relax at hotel / spa / leisure
- Day 5: Visit a popular park / botanical, City tour (key landmarks + viewpoints), a lake / park + sunset
- Day 6: Guided heritage walk in the old city area, Shopping at a local market / mall, Street food + shopping street

Total Budget: ₹45,803

---

## 📌 Key Takeaways
```
- Demonstrates Agentic AI reasoning using LangChain
- Clean separation of tools and agent logic
- Real-world use of JSON datasets + live APIs
- Production-style project structure with testing
- User-friendly Streamlit interface with explainable outputs

```
---

## Future Enhancements
```
- Add real flight & hotel APIs
- Multi-city trip planning
- User profiles & saved trips
- Advanced optimization (time vs cost trade-offs)
- Deployment on Streamlit Cloud or Hugging Face Spaces

```
---

## 📄 License
```
- MIT License
- Copyright (c) 2025 Shyam SR
```
---
