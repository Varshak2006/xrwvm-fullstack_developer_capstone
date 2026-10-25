
const express = require('express');
const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const port = 3030;

app.use(cors());
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

const reviewsPath = path.join(__dirname, 'data', 'reviews.json');
const dealershipsPath = path.join(__dirname, 'data', 'dealerships.json');

const reviewsData = JSON.parse(fs.readFileSync(reviewsPath, 'utf8'));
const dealershipsData = JSON.parse(fs.readFileSync(dealershipsPath, 'utf8'));

const Reviews = require('./review');
const Dealerships = require('./dealership');

app.get('/', (req, res) => {
  res.send('Welcome to the Mongoose API');
});

app.get('/fetchReviews', async (req, res) => {
  try {
    res.json(await Reviews.find());
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

app.get('/fetchReviews/dealer/:id', async (req, res) => {
  try {
    res.json(await Reviews.find({ dealership: Number(req.params.id) }));
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

// Fetch all dealerships
app.get('/fetchDealers', async (req, res) => {
  try {
    res.json(await Dealerships.find());
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealerships' });
  }
});

// Fetch dealerships by state name or abbreviation
app.get('/fetchDealers/:state', async (req, res) => {
  try {
    const requestedState = decodeURIComponent(req.params.state).trim();
    const dealers = await Dealerships.find({
      $or: [
        { state: { $regex: `^${requestedState}$`, $options: 'i' } },
        { st: { $regex: `^${requestedState}$`, $options: 'i' } }
      ]
    });
    res.json(dealers);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealerships by state' });
  }
});

// Fetch one dealership by numeric ID
app.get('/fetchDealer/:id', async (req, res) => {
  try {
    const dealer = await Dealerships.findOne({ id: Number(req.params.id) });
    if (!dealer) {
      return res.status(404).json({ error: 'Dealership not found' });
    }
    res.json(dealer);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealership' });
  }
});

// Insert a review
app.post('/insert_review', async (req, res) => {
  try {
    const data = typeof req.body === 'string'
      ? JSON.parse(req.body)
      : req.body;

    const latestReview = await Reviews.findOne().sort({ id: -1 });
    const newId = latestReview ? latestReview.id + 1 : 1;

    const review = new Reviews({
      id: newId,
      name: data.name,
      dealership: data.dealership,
      review: data.review,
      purchase: data.purchase,
      purchase_date: data.purchase_date,
      car_make: data.car_make,
      car_model: data.car_model,
      car_year: data.car_year
    });

    res.json(await review.save());
  } catch (error) {
    console.error('Review insertion failed:', error.message);
    res.status(500).json({ error: 'Error inserting review' });
  }
});

async function startServer() {
  try {
    await mongoose.connect('mongodb://127.0.0.1:27017/', {
      dbName: 'dealershipsDB'
    });

    await Reviews.deleteMany({});
    await Reviews.insertMany(reviewsData.reviews);

    await Dealerships.deleteMany({});
    await Dealerships.insertMany(dealershipsData.dealerships);

    console.log('Database connected and dealership/review data loaded.');

    app.listen(port, '0.0.0.0', () => {
      console.log(`Server is running on http://localhost:${port}`);
    });
  } catch (error) {
    console.error('Failed to initialize API:', error);
    process.exit(1);
  }
}

startServer();
