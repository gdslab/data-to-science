public interface DiscountStrategy {
    double apply(double price);
}

public class PercentageDiscount implements DiscountStrategy {
    private final double percent;
    public PercentageDiscount(double percent) { this.percent = percent; }
    public double apply(double price) { return price * (1 - percent / 100); }
}

public class FixedDiscount implements DiscountStrategy {
    private final double amount;
    public FixedDiscount(double amount) { this.amount = amount; }
    public double apply(double price) { return price - amount; }
}

public class PriceCalculator {
    private DiscountStrategy strategy;
    public PriceCalculator(DiscountStrategy strategy) { this.strategy = strategy; }
    public double calculate(double price) { return strategy.apply(price); }
    public void setStrategy(DiscountStrategy strategy) { this.strategy = strategy; }
}

public class Main {
    public static void main(String[] args) {
        PriceCalculator calc = new PriceCalculator(new PercentageDiscount(10));
        System.out.println("10% off: " + calc.calculate(100));
        calc.setStrategy(new FixedDiscount(15));
        System.out.println("$15 off: " + calc.calculate(100));
    }
}
