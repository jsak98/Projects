using CarRentalAPI.Models;
using FluentValidation;

namespace CarRentalAPI.Validators
{
    public class BookingValidator : AbstractValidator<Booking>
    {
        public BookingValidator()
        {
            RuleFor(b => b.BookingId)
                .NotEmpty().WithMessage("Booking ID is required.")
                .MaximumLength(10).WithMessage("Booking ID cannot exceed 10 characters.");

            RuleFor(b => b.CustomerName)
                .NotEmpty().WithMessage("Customer name is required.")
                .MaximumLength(50).WithMessage("Customer name cannot exceed 50 characters.");

            RuleFor(b => b.CarModel)
                .NotEmpty().WithMessage("Car model is required.")
                .MaximumLength(50).WithMessage("Car model cannot exceed 50 characters.");

            RuleFor(b => b.PickupDate)
                .Must(date => date >= DateOnly.FromDateTime(DateTime.Now))
                .WithMessage("Pickup date cannot be in the past.");

            RuleFor(b => b.ReturnDate)
                .NotEmpty().WithMessage("Return date is required.")
                .GreaterThan(b => b.PickupDate).WithMessage("Return date must be after pickup date.");

            RuleFor(b => b.DailyRate)
                .GreaterThan(0).WithMessage("Daily rate must be greater than zero.");

        }
    }
}