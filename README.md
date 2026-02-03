# Six Nations Bookie

A betting simulation engine for Six Nations rugby. Create linked spread markets for team championship points with friends.

## Quick Start with GitHub Codespaces (Recommended)

1. Click the green **Code** button on GitHub
2. Select **Codespaces** tab
3. Click **Create codespace on main**
4. Wait for setup to complete (~1 minute)
5. Run the demo:
   ```bash
   ./run-demo.sh
   ```

That's it! The environment comes pre-configured with all dependencies.

## What You Can Do

### Run the Demo
```bash
./run-demo.sh
```
Shows the market maker in action: calibration, quotes for all 6 teams, and a sample trade with linked price movements.

### Start the Web API
```bash
./run-api.sh
```
Launches a FastAPI server at `http://localhost:8000` with interactive docs at `/docs`.

## Local Setup (Alternative)

```bash
git clone https://github.com/RussOxley/SixNationsBookie.git
cd SixNationsBookie/sixnations_bookie_assets_v2
pip install -r requirements.txt
python demo_sixnations_points_market.py
```

## How It Works

- **Monte Carlo Simulation**: Simulates thousands of tournament outcomes to price markets
- **Linked Markets**: All 6 team markets are connected via covariance - if France goes up, others adjust
- **Market Making**: Bid/ask quotes adjust based on house inventory to prevent manipulation
- **Risk Management**: Margin calculations ensure users can cover worst-case outcomes

## Project Structure

```
sixnations_bookie_assets_v2/
├── demo_sixnations_points_market.py  # Working demo
├── sixnations_bookie/                # Core engine
│   ├── simulator.py                  # Monte Carlo tournament sim
│   ├── market_maker.py               # Linked market pricing
│   ├── calibration.py                # Fit teams to predictions
│   └── risk.py                       # Position & margin tracking
└── backend_skeleton/                 # FastAPI HTTP API
```

## Documentation

- [Developer Guide](sixnations_bookie_assets_v2/DEVELOPER_GUIDE.md) - Detailed implementation docs
- [API Docs](http://localhost:8000/docs) - Interactive API documentation (when running)
