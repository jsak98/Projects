using Microsoft.EntityFrameworkCore;
using CarRentalAPI.Models;

namespace CarRentalAPI.Data
{
    public class CarRentalContext : DbContext
    {
        public CarRentalContext(DbContextOptions<CarRentalContext> options) : base(options)
        {
        }

        public DbSet<Booking> Bookings { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            // Configure BookingId as the primary key
            modelBuilder.Entity<Booking>()
                .HasKey(b => b.BookingId);

            // Store PickupDate as DateOnly in database
            modelBuilder.Entity<Booking>()
                .Property(b => b.PickupDate)
                .HasConversion(
                    d => d.ToDateTime(TimeOnly.MinValue),  // DateOnly -> DateTime for DB
                    d => DateOnly.FromDateTime(d)          // DateTime -> DateOnly for EF
                )
                .HasColumnType("date");

            // Store ReturnDate as DateOnly in database
            modelBuilder.Entity<Booking>()
                .Property(b => b.ReturnDate)
                .HasConversion(
                    d => d.ToDateTime(TimeOnly.MinValue),
                    d => DateOnly.FromDateTime(d)
                )
                .HasColumnType("date");
        }
    }
}
