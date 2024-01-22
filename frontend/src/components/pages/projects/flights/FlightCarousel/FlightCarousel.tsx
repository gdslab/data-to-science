import { Swiper, SwiperSlide } from 'swiper/react';

// swiper styles
import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';
import './FlightCarousel.css';

// swiper required modules
import { Pagination, Navigation } from 'swiper/modules';

import FlightCard from '../FlightCard';
import { Flight } from '../../ProjectDetail';

export default function FlightCarousel({ flights }: { flights: Flight[] }) {
  return (
    <Swiper
      slidesPerView={5}
      spaceBetween={30}
      centeredSlides={true}
      navigation={true}
      pagination={{ clickable: true }}
      modules={[Pagination, Navigation]}
    >
      {flights.map((flight) => (
        <SwiperSlide key={flight.id}>
          <FlightCard flight={flight} />
        </SwiperSlide>
      ))}
    </Swiper>
  );
}
