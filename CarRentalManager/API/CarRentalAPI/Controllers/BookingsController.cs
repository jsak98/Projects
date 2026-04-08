using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CarRentalAPI.Data;
using CarRentalAPI.Models;

namespace CarRentalAPI.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class BookingsController : ControllerBase
    {
        private readonly CarRentalContext _context;
        private readonly ILogger<BookingsController> _logger;

        public BookingsController(CarRentalContext context, ILogger<BookingsController> logger)
        {
            _context = context;
            _logger = logger;
        }

        /// <summary>Get all bookings.</summary>
        [HttpGet]
        [ProducesResponseType(StatusCodes.Status200OK)]
        public async Task<ActionResult<IEnumerable<Booking>>> GetAll()
        {
            _logger.LogInformation("Fetching all bookings...");
            var bookings = await _context.Bookings.ToListAsync();
            return Ok(bookings);
        }

        /// <summary>Get a booking by ID.</summary>
        [HttpGet("{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<Booking>> GetById(string id)
        {
            _logger.LogInformation("Fetching booking with ID: {BookingId}", id);
            var booking = await _context.Bookings.FindAsync(id);
            if (booking == null)
            {
                _logger.LogWarning("Booking not found: {BookingId}", id);
                return NotFound(new { message = $"Booking with id '{id}' not found." });
            }

            return Ok(booking);
        }

        /// <summary>Add a new booking.</summary>
        [HttpPost]
        [ProducesResponseType(typeof(Booking), StatusCodes.Status201Created)]
        [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
        [ProducesResponseType(StatusCodes.Status409Conflict)]
        public async Task<IActionResult> Create([FromBody] Booking booking)
        {
            _logger.LogInformation("Creating booking with ID: {BookingId}", booking.BookingId);

            if (await _context.Bookings.AnyAsync(b => b.BookingId == booking.BookingId))
            {
                _logger.LogWarning("Conflict: Booking with ID already exists: {BookingId}", booking.BookingId);
                return Conflict(new { message = $"Booking with id '{booking.BookingId}' already exists." });
            }

            _context.Bookings.Add(booking);
            await _context.SaveChangesAsync();

            _logger.LogInformation("Booking created successfully: {BookingId}", booking.BookingId);
            return CreatedAtAction(nameof(GetById), new { id = booking.BookingId }, booking);
        }

        [HttpPut("{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> Update(string id, [FromBody] Booking updatedBooking)
        {
            if (id != updatedBooking.BookingId)
            {
                _logger.LogWarning("Bad Request: Booking ID mismatch.");
                return BadRequest(new { message = "Booking ID mismatch." });
            }

            var booking = await _context.Bookings.FindAsync(id);
            if (booking == null)
            {
                _logger.LogWarning("Booking not found for update: {BookingId}", id);
                return NotFound(new { message = $"Booking with id '{id}' not found." });
            }

            // Update fields
            booking.CustomerName = updatedBooking.CustomerName;
            booking.CarModel = updatedBooking.CarModel;
            booking.PickupDate = updatedBooking.PickupDate; // just assign DateOnly
            booking.ReturnDate = updatedBooking.ReturnDate; // just assign DateOnly
            booking.DailyRate = updatedBooking.DailyRate;

            await _context.SaveChangesAsync();

            _logger.LogInformation("Booking updated successfully: {BookingId}", id);
            return Ok(booking);
        }


        /// <summary>Delete a booking.</summary>
        [HttpDelete("{id}")]
        [ProducesResponseType(StatusCodes.Status204NoContent)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> Delete(string id)
        {
            var booking = await _context.Bookings.FindAsync(id);
            if (booking == null)
            {
                _logger.LogWarning("Booking not found for delete: {BookingId}", id);
                return NotFound(new { message = $"Booking with id '{id}' not found." });
            }

            _context.Bookings.Remove(booking);
            await _context.SaveChangesAsync();

            _logger.LogInformation("Booking deleted successfully: {BookingId}", id);
            return NoContent();
        }
    }
}