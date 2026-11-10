package exp01;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Measurement harness for Experiment 1 (Bubble Inc. sorting library).
 *
 * <p>Factors (independent variables):
 * <ul>
 *   <li>algorithm: PassPerItem, UntilNoChange, WhileNeeded</li>
 *   <li>input type: SORTED, REVERSE, RANDOM</li>
 *   <li>array size: configurable (default 1000, 5000, 10000)</li>
 * </ul>
 *
 * <p>Dependent variable: wall-clock time of a single {@code sort()} call in
 * nanoseconds, measured with {@link System#nanoTime()}.
 *
 * <p>Measurement protocol:
 * <ol>
 *   <li>All input arrays are generated before measuring, from a fixed seed
 *       (reproducible). RANDOM input uses a different permutation for every
 *       repetition r, and all three algorithms sort the same permutation for
 *       the same r (seed = seed * 1_000_003 + size * 1000 + r).</li>
 *   <li>Warm-up: every (algorithm, input type, size) combination is executed
 *       {@code warmup} times; these runs are discarded so that the JIT compiler
 *       has compiled the sorting methods before measurement starts.</li>
 *   <li>Measurement: every combination is executed {@code reps} times. All
 *       runs are put in one list that is shuffled with the fixed seed, so that
 *       systematic drifts (e.g. thermal throttling, background activity) do not
 *       affect one algorithm more than another.</li>
 *   <li>Before each timed run a fresh copy of the input is made and
 *       {@code System.gc()} is requested; neither is included in the timing.</li>
 *   <li>After each run the result is checked to be sorted (outside the timing).
 *       This also prevents the JIT from removing the sort as dead code.</li>
 * </ol>
 *
 * <p>Usage: {@code java -cp build exp01.Benchmark [--reps=N] [--warmup=N]
 * [--sizes=a,b,c] [--seed=N] [--out=path] [--env=path]}
 */
public final class Benchmark {

    /** Initial order of the elements in the array to sort. */
    enum InputType { SORTED, REVERSE, RANDOM }

    /** One timed execution to perform. */
    private static final class Run {
        final String algorithm;
        final InputType inputType;
        final int size;
        final int repetition;

        Run(String algorithm, InputType inputType, int size, int repetition) {
            this.algorithm = algorithm;
            this.inputType = inputType;
            this.size = size;
            this.repetition = repetition;
        }
    }

    private Benchmark() { }

    public static void main(String[] args) throws IOException {
        Map<String, String> opts = parseArgs(args);
        int reps = Integer.parseInt(opts.getOrDefault("reps", "30"));
        int warmup = Integer.parseInt(opts.getOrDefault("warmup", "10"));
        long seed = Long.parseLong(opts.getOrDefault("seed", "42"));
        String out = opts.getOrDefault("out", "data/results.csv");
        String env = opts.getOrDefault("env", "data/environment.txt");
        List<Integer> sizes = new ArrayList<>();
        for (String s : opts.getOrDefault("sizes", "1000,5000,10000").split(",")) {
            sizes.add(Integer.parseInt(s.trim()));
        }

        Map<String, Sorter<Integer>> sorters = new LinkedHashMap<>();
        sorters.put("PassPerItem", new BubbleSortPassPerItem<>());
        sorters.put("UntilNoChange", new BubbleSortUntilNoChange<>());
        sorters.put("WhileNeeded", new BubbleSortWhileNeeded<>());

        // Generate every input before measuring; each run sorts a fresh copy.
        // Repetition r of a (type, size) condition uses the same array for all
        // algorithms; RANDOM arrays differ between repetitions.
        Map<String, Integer[]> inputs = new HashMap<>();
        for (int size : sizes) {
            for (InputType type : InputType.values()) {
                for (int r = 1; r <= reps; r++) {
                    Random rnd = new Random(seed * 1_000_003L + size * 1000L + r);
                    inputs.put(key(type, size, r), generate(type, size, rnd));
                }
            }
        }

        writeEnvironment(env, reps, warmup, seed, sizes);

        // Warm-up phase (results discarded).
        System.err.println("Warm-up: " + warmup + " run(s) per combination");
        for (int w = 0; w < warmup; w++) {
            for (Map.Entry<String, Sorter<Integer>> s : sorters.entrySet()) {
                for (int size : sizes) {
                    for (InputType type : InputType.values()) {
                        timeOnce(s.getValue(), inputs.get(key(type, size, 1)));
                    }
                }
            }
        }

        // Measurement phase: all runs in a seeded random order.
        List<Run> runs = new ArrayList<>();
        for (String algorithm : sorters.keySet()) {
            for (int size : sizes) {
                for (InputType type : InputType.values()) {
                    for (int r = 1; r <= reps; r++) {
                        runs.add(new Run(algorithm, type, size, r));
                    }
                }
            }
        }
        Collections.shuffle(runs, new Random(seed));

        try (PrintWriter csv = new PrintWriter(new FileWriter(out))) {
            csv.println("run_order,algorithm,input_type,size,repetition,time_ns");
            int order = 0;
            for (Run run : runs) {
                order++;
                long ns = timeOnce(sorters.get(run.algorithm),
                        inputs.get(key(run.inputType, run.size, run.repetition)));
                csv.printf("%d,%s,%s,%d,%d,%d%n", order, run.algorithm,
                        run.inputType, run.size, run.repetition, ns);
                if (order % 50 == 0 || order == runs.size()) {
                    csv.flush();
                    System.err.println("Measured " + order + "/" + runs.size());
                }
            }
        }
        System.err.println("Results written to " + out);
    }

    /**
     * Sorts a fresh copy of {@code input} and returns the elapsed time in ns.
     * Copying, garbage collection and the correctness check are not timed.
     */
    private static long timeOnce(Sorter<Integer> sorter, Integer[] input) {
        Integer[] copy = input.clone();
        System.gc();
        long start = System.nanoTime();
        sorter.sort(copy);
        long end = System.nanoTime();
        if (!isSorted(copy)) {
            throw new IllegalStateException(sorter.getClass().getSimpleName()
                    + " did not sort the array");
        }
        return end - start;
    }

    /** Builds an array of the distinct values 0..size-1 in the given order. */
    static Integer[] generate(InputType type, int size, Random random) {
        Integer[] a = new Integer[size];
        for (int i = 0; i < size; i++) {
            a[i] = i;
        }
        switch (type) {
            case SORTED:
                break;
            case REVERSE:
                for (int i = 0; i < size; i++) {
                    a[i] = size - 1 - i;
                }
                break;
            case RANDOM:
                // Fisher-Yates shuffle with the seeded generator.
                for (int i = size - 1; i > 0; i--) {
                    int j = random.nextInt(i + 1);
                    Integer t = a[i];
                    a[i] = a[j];
                    a[j] = t;
                }
                break;
            default:
                throw new IllegalArgumentException(type.toString());
        }
        return a;
    }

    private static boolean isSorted(Integer[] a) {
        for (int i = 1; i < a.length; i++) {
            if (a[i - 1].compareTo(a[i]) > 0) {
                return false;
            }
        }
        return true;
    }

    private static String key(InputType type, int size, int repetition) {
        return type + "_" + size + "_" + repetition;
    }

    /** Records the measurement environment for reproducibility. */
    private static void writeEnvironment(String path, int reps, int warmup,
            long seed, List<Integer> sizes) throws IOException {
        Runtime rt = Runtime.getRuntime();
        try (PrintWriter w = new PrintWriter(new FileWriter(path))) {
            w.println("timestamp=" + Instant.now());
            w.println("java.version=" + System.getProperty("java.version"));
            w.println("java.vm.name=" + System.getProperty("java.vm.name"));
            w.println("java.vm.version=" + System.getProperty("java.vm.version"));
            w.println("os.name=" + System.getProperty("os.name"));
            w.println("os.version=" + System.getProperty("os.version"));
            w.println("os.arch=" + System.getProperty("os.arch"));
            w.println("available.processors=" + rt.availableProcessors());
            w.println("max.heap.bytes=" + rt.maxMemory());
            w.println("reps=" + reps);
            w.println("warmup=" + warmup);
            w.println("seed=" + seed);
            w.println("sizes=" + sizes);
        }
    }

    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> m = new HashMap<>();
        for (String a : args) {
            if (!a.startsWith("--") || !a.contains("=")) {
                throw new IllegalArgumentException("Bad argument: " + a);
            }
            int eq = a.indexOf('=');
            m.put(a.substring(2, eq), a.substring(eq + 1));
        }
        return m;
    }
}
