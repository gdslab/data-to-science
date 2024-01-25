import { Swiper, SwiperSlide } from 'swiper/react';

// swiper styles
import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';
import './FlightCarousel.css';

// swiper required modules
import { Pagination, Mousewheel, Navigation } from 'swiper/modules';

import FlightCard from './FlightCard';
import { Flight } from '../../ProjectDetail';

import { sorter } from '../../../../utils';
import useWindowDimensions from '../../../../hooks/useWindowDimensions';

function getSlidesPerView(width: number): number {
  if (width > 1600) {
    return 5;
  } else if (width > 1280 && width <= 1600) {
    return 4;
  } else if (width > 1024 && width <= 1280) {
    return 3;
  } else if (width > 640 && width <= 1024) {
    return 2;
  } else {
    return 1;
  }
}

export default function FlightCarousel({ flights }: { flights: Flight[] }) {
  const { width } = useWindowDimensions();

  return (
    <>
      <Swiper
        slidesPerView={getSlidesPerView(width)}
        spaceBetween={30}
        centeredSlides={true}
        mousewheel={true}
        navigation={true}
        pagination={{ clickable: true }}
        modules={[Pagination, Mousewheel, Navigation]}
      >
        {flights
          .sort((a, b) =>
            sorter(new Date(a.acquisition_date), new Date(b.acquisition_date), 'asc')
          )
          .map((flight) => (
            <SwiperSlide key={flight.id}>
              <FlightCard flight={flight} />
            </SwiperSlide>
          ))}
      </Swiper>
    </>
  );
}
