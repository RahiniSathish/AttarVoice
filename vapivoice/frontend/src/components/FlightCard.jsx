import React from 'react';
import './FlightCard.css';

const FlightCard = ({ flight }) => {
  // Extract flight data
  const origin = flight.origin || 'N/A';
  const destination = flight.destination || 'N/A';
  const airline = flight.airline || 'N/A';
  const flightNumber = flight.flight_number || 'N/A';
  const departureTime = flight.departure_time || 'N/A';
  const arrivalTime = flight.arrival_time || 'N/A';
  const price = typeof flight.price === 'number' ? flight.price.toLocaleString('en-IN') : flight.price || 'N/A';
  const duration = flight.duration || 'N/A';

  return (
    <div className="flight-card-modern">
      {/* Route Header */}
      <div className="flight-route">
        <span className="route-text">{origin} → {destination}</span>
      </div>

      {/* Airline Info */}
      <div className="flight-airline">
        <span className="airline-text">{airline} | {flightNumber}</span>
      </div>

      {/* Flight Details - Time, Price, Duration */}
      <div className="flight-details">
        <div className="detail-item">
          <span className="detail-icon">🕐</span>
          <span className="detail-text">{departureTime} - {arrivalTime}</span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">💰</span>
          <span className="detail-text">₹{price}</span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">⏱️</span>
          <span className="detail-text">{duration}</span>
        </div>
      </div>

      {/* Book Button */}
      <button className="book-button">
        Book Now ✈️
      </button>
    </div>
  );
};

export default FlightCard;
