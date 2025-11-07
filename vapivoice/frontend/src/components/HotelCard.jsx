import React from 'react';
import './HotelCard.css';

const HotelCard = ({ hotel }) => {
  // Extract hotel data
  const name = hotel.name || 'N/A';
  const location = hotel.location || 'N/A';
  const stars = hotel.stars || 0;
  const type = hotel.type || 'Hotel';
  const reviews = hotel.reviews || 'No reviews available';
  const googleMapsUrl = hotel.google_maps_url || hotel.url || '#';
  const price = hotel.price || 'Contact for pricing';

  // Render star rating
  const renderStars = (count) => {
    return '⭐'.repeat(Math.min(count, 5));
  };

  return (
    <div className="hotel-card-modern">
      {/* Hotel Name */}
      <div className="hotel-name-header">
        <h3 className="hotel-name">{name}</h3>
        <span className="hotel-type-badge">{type}</span>
      </div>

      {/* Stars */}
      <div className="hotel-stars-section">
        <span className="hotel-stars">{renderStars(stars)}</span>
      </div>

      {/* Hotel Details */}
      <div className="hotel-details">
        <div className="detail-item">
          <span className="detail-icon">📍</span>
          <span className="detail-text">{location}</span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">💬</span>
          <span className="detail-text">{reviews}</span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">💰</span>
          <span className="detail-text">{price}</span>
        </div>
      </div>

      {/* View Button */}
      <a 
        href={googleMapsUrl} 
        target="_blank" 
        rel="noopener noreferrer"
        className="view-button"
      >
        View on Maps 🗺️
      </a>
    </div>
  );
};

export default HotelCard;
