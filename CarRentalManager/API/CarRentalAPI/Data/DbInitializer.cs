using CarRentalAPI.Models;

namespace CarRentalAPI.Data
{
    public static class DbInitializer
    {
        public static void Initialize(CarRentalContext context)
        {
            // Ensure database is created
            context.Database.EnsureCreated();

            // If there are already bookings, no need to seed
            if (context.Bookings.Any())
                return;

            var bookings = new Booking[]
            {
                new Booking { BookingId = "B001", CustomerName = "Raj",   CarModel = "Toyota Corolla", PickupDate = new DateOnly(2025, 8, 15), ReturnDate = new DateOnly(2025, 8, 18), DailyRate = 55 },
                new Booking { BookingId = "B002", CustomerName = "Anita", CarModel = "Honda Civic",    PickupDate = new DateOnly(2025, 8, 14), ReturnDate = new DateOnly(2025, 8, 16), DailyRate = 60 },
                new Booking { BookingId = "B003", CustomerName = "Sam",   CarModel = "Honda City",     PickupDate = new DateOnly(2025, 8, 16), ReturnDate = new DateOnly(2025, 8, 19), DailyRate = 70 }

            };

            context.Bookings.AddRange(bookings);
            context.SaveChanges();
        }
    }
}