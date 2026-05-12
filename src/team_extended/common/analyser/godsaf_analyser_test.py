from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.common.analyser.godsaf_analyser import GoDsAFAnalysisNode


if __name__ == "__main__":
    af = GoDsAFService()

    af.add_team("tl")
    af.add_team("tws")

    af.add_domain("d_culture", 25)
    af.add_domain("d_ops", 80)

    af.add_goal("g_innovation", {"d_culture": 10, "d_ops": 30})
    af.add_goal("g_retention", {"d_culture": 15, "d_ops": 55})

    af.add_argument(
        "a_culture",
        "tl",
        ["d_culture"],
        {"g_innovation": ["d_culture"], "g_retention": ["d_culture"]},
    )
    af.add_argument("a_innovation", "tl", ["d_ops"], {"g_innovation": ["d_ops"]})
    af.add_argument("a_tools", "tl", ["d_ops"], {"g_innovation": ["d_ops"]})
    af.add_argument(
        "a_talent", "tws", ["d_culture"], {"g_retention": ["d_culture"]}, ["a_culture"]
    )
    af.add_argument(
        "a_burnout", "tws", ["d_ops"], {"g_retention": ["d_ops"]}, ["a_innovation"]
    )
    af.add_attack("a_tools", "a_burnout")

    analyzer = GoDsAFAnalysisNode(af)

    print("STRATEGY ANALYSIS")
    print("=" * 60)

    tl_strategy = analyzer.analyze_team_strategy("tl")
    print(tl_strategy.analysis_summary)
    print()

    tws_strategy = analyzer.analyze_team_strategy("tws")
    print(tws_strategy.analysis_summary)
    print()

    print(analyzer.compare_team_strategies("tl", "tws"))
    print()

    print(analyzer.get_detailed_ugn_analysis("tl"))
    print()
    print(analyzer.get_detailed_ugn_analysis("tws"))
