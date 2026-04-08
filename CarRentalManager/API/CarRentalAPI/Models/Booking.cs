using System.ComponentModel.DataAnnotations;

namespace CarRentalAPI.Models;

public class Booking
{
    [Key]
    [Required(ErrorMessage = "BookingId is required.")]
    public string BookingId { get; set; } = string.Empty;

    [Required(ErrorMessage = "Customer name is required.")]
    [StringLength(100, ErrorMessage = "Customer name must be under 100 characters.")]
    public string CustomerName { get; set; } = string.Empty;

    [Required(ErrorMessage = "Car model is required.")]
    [StringLength(100, ErrorMessage = "Car model must be under 100 characters.")]
    public string CarModel { get; set; } = string.Empty;

    [Required(ErrorMessage = "Pickup date is required.")]
    public DateOnly PickupDate { get; set; }

    [Required(ErrorMessage = "Return date is required.")]
    public DateOnly ReturnDate { get; set; }

    [Range(1, 5000, ErrorMessage = "Daily rate must be between 1 and 5000.")]
    public decimal DailyRate { get; set; }
}
