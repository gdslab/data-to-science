import { Swiper, SwiperSlide } from 'swiper/react';

// swiper styles
import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';
import './FlightCarousel.css';

// swiper required modules
import { Pagination, Mousewheel, Navigation } from 'swiper/modules';

import FlightCard from '../FlightCard';
import { Flight } from '../../ProjectDetail';

import useWindowDimensions from '../../../../hooks/useWindowDimensions';

export default function FlightCarousel({ flights }: { flights: Flight[] }) {
  const { width } = useWindowDimensions();
  console.log(width);
  return (
    <>
      <Swiper
        slidesPerView={width <= 1281 ? 3 : width <= 1600 ? 4 : 5}
        spaceBetween={30}
        centeredSlides={true}
        mousewheel={true}
        navigation={true}
        pagination={{ clickable: true }}
        modules={[Pagination, Mousewheel, Navigation]}
      >
        {flights.map((flight) => (
          <SwiperSlide key={flight.id}>
            <FlightCard flight={flight} />
          </SwiperSlide>
        ))}
      </Swiper>
    </>
  );
}
